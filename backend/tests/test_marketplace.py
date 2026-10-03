import pytest
from uuid import uuid4
from datetime import datetime, timezone

from backend.app.services.marketplace.exceptions import (
    MarketplaceException,
    PackageValidationError,
    PackageSecurityBlockedError,
    PackageIncompatibleError,
    DependencyResolutionError,
    RollbackNotAllowedError,
    PackageRevokedError,
)
from backend.app.services.marketplace.validator import PackageValidator
from backend.app.services.marketplace.security_scanner import MarketplaceSecurityScanner
from backend.app.services.marketplace.dependencies import DependencyResolver
from backend.app.services.marketplace.compatibility import CompatibilityChecker
from backend.app.services.marketplace.permissions import MarketplacePermissionManager
from backend.app.services.marketplace.builder import MarketplacePackageBuilder
from backend.app.services.marketplace.ratings import MarketplaceRatingCalculator
from backend.app.services.marketplace.reviews import MarketplaceReviewService


class TestMarketplaceSecurityAndValidation:
    """Tests deterministic validation and security scanning of untrusted packages."""

    def test_valid_manifest_passes_validation(self):
        manifest = {
            "schema_version": "1.0",
            "package": {
                "name": "Document Analyzer Pack",
                "version": "1.2.0",
                "type": "work_pack",
            },
            "compatibility": {
                "platform_min_version": "1.0.0",
                "model_capabilities": ["structured_output"],
            },
            "components": [
                {"name": "Doc Workflow", "type": "workflow", "identifier": "wf_doc"},
                {"name": "Summary Prompt", "type": "prompt", "identifier": "prompt_sum"},
            ],
            "permissions": [
                {"scope": "documents:read", "description": "Read tenant documents"},
                {"scope": "tasks:run", "description": "Execute tasks"},
            ],
            "dependencies": [],
            "configuration": {
                "variables": {
                    "batch_size": {"type": "integer", "default": 10},
                }
            },
        }

        # Should validate without raising PackageValidationError
        warnings = PackageValidator.validate_manifest(manifest)
        assert isinstance(warnings, list)

    def test_invalid_semantic_version_rejected(self):
        manifest = {
            "package": {"name": "Bad Version", "version": "v1.2", "type": "workflow"},
            "components": [],
        }
        with pytest.raises(PackageValidationError):
            PackageValidator.validate_manifest(manifest)

    def test_arbitrary_code_injection_rejected(self):
        # Manifest attempting to smuggle python code
        manifest = {
            "package": {"name": "Malicious Code", "version": "1.0.0", "type": "workflow"},
            "components": [
                {
                    "name": "Bad Step",
                    "type": "workflow_step",
                    "identifier": "step_bad",
                    "code": "import os; os.system('echo compromised')",
                }
            ],
        }
        with pytest.raises(PackageValidationError) as exc:
            PackageValidator.validate_manifest(manifest)
        assert "validation failed" in str(exc.value)

    def test_arbitrary_shell_or_child_process_rejected(self):
        manifest = {
            "package": {"name": "JS Exploit", "version": "1.0.0", "type": "workflow"},
            "components": [
                {
                    "name": "Bad Step",
                    "type": "workflow_step",
                    "identifier": "step_bad",
                    "script": "child_process.execSync('whoami')",
                }
            ],
        }
        with pytest.raises(PackageValidationError) as exc:
            PackageValidator.validate_manifest(manifest)
        assert "validation failed" in str(exc.value)

    def test_security_scanner_detects_credentials(self):
        manifest = {
            "package": {"name": "Leaky Package", "version": "1.0.0", "type": "prompt"},
            "components": [],
            "configuration": {
                "variables": {
                    "api_key": {"default": "sk-proj-abc123456789012345678901234567890"},
                }
            },
        }
        status, findings = MarketplaceSecurityScanner.scan_manifest(manifest)
        assert "blocked" in str(status).lower()
        assert any("credential" in f.lower() or "secret" in f.lower() for f in findings)

    def test_security_scanner_detects_ssrf(self):
        manifest = {
            "package": {"name": "SSRF Package", "version": "1.0.0", "type": "connector_template"},
            "components": [],
            "configuration": {
                "variables": {
                    "endpoint": {"default": "http://169.254.169.254/latest/meta-data/"},
                }
            },
        }
        status, findings = MarketplaceSecurityScanner.scan_manifest(manifest)
        assert "blocked" in str(status).lower()
        assert any("blocked" in f.lower() or "ssrf" in f.lower() or "host" in f.lower() for f in findings)

    def test_security_scanner_detects_path_traversal(self):
        manifest = {
            "package": {"name": "Traversal Package", "version": "1.0.0", "type": "tool"},
            "components": [
                {"name": "File Read", "type": "tool_definition", "identifier": "../../etc/passwd"}
            ],
        }
        status, findings = MarketplaceSecurityScanner.scan_manifest(manifest)
        assert "blocked" in str(status).lower()
        assert any("traversal" in f.lower() for f in findings)


class TestDependencyResolution:
    """Tests deterministic resolution of package dependencies and cycle detection."""

    def test_linear_dependencies_pass(self):
        dependencies = [
            {"dependency_type": "package", "dependency_identifier": "pkg_a", "version_constraint": ">=1.0.0"},
            {"dependency_type": "tool", "dependency_identifier": "web_search", "version_constraint": "*"},
        ]
        resolved = DependencyResolver.resolve_dependencies(dependencies)
        assert len(resolved) == 2
        assert DependencyResolver.validate_version_constraint("1.2.0", ">=1.0.0") is True

    def test_dependency_cycle_detected(self):
        # A depends on B, B depends on C, C depends on A
        dep_graph = {
            "pkg_a": ["pkg_b"],
            "pkg_b": ["pkg_c"],
            "pkg_c": ["pkg_a"],
        }
        with pytest.raises(DependencyResolutionError) as exc:
            DependencyResolver.detect_cycle("pkg_a", dep_graph)
        assert "Circular dependency detected" in str(exc.value)


class TestCompatibilityChecker:
    """Tests runtime compatibility verification without subjective rankings."""

    def test_compatible_platform_and_capabilities(self):
        compat_decl = {
            "platform_min_version": "1.0.0",
            "model_capabilities": ["structured_output", "vision"],
        }
        status, issues = CompatibilityChecker.check_compatibility(compat_decl)
        assert status == "compatible"
        assert len(issues) == 0

    def test_incompatible_platform_version(self):
        compat_decl = {
            "platform_min_version": "99.0.0",
        }
        status, issues = CompatibilityChecker.check_compatibility(compat_decl)
        assert status == "incompatible"
        assert any("Platform version" in issue for issue in issues)

    def test_incompatible_model_capability(self):
        compat_decl = {
            "model_capabilities": ["quantum_telepathy"],
        }
        status, issues = CompatibilityChecker.check_compatibility(compat_decl)
        assert status == "incompatible"
        assert any("quantum_telepathy" in issue for issue in issues)


class TestPermissionsAndPreview:
    """Verifies permission mapping and package preview generation."""

    def test_permissions_mapping(self):
        declared = [
            {"scope": "workflows:read", "description": "Read workflows"},
            {"scope": "marketplace:install", "description": "Install extension"},
        ]
        valid_perms, invalid = MarketplacePermissionManager.validate_declared_permissions(declared)
        assert len(valid_perms) == 2
        assert len(invalid) == 0

    def test_invalid_scope_detected(self):
        declared = [
            {"scope": "superadmin:root_access", "description": "Fake scope"},
        ]
        valid_perms, invalid = MarketplacePermissionManager.validate_declared_permissions(declared)
        assert "superadmin:root_access" in invalid

    def test_package_builder_preview(self):
        manifest = {
            "package": {"name": "Preview Pack", "version": "1.0.0", "type": "work_pack"},
            "components": [{"name": "Step 1", "type": "workflow_step", "identifier": "s1"}],
            "permissions": [{"scope": "tasks:read", "description": "Read tasks"}],
            "dependencies": [],
            "configuration": {"variables": {"depth": {"type": "integer", "default": 2}}},
        }
        preview = MarketplacePackageBuilder.preview_package(manifest)
        assert preview["component_count"] == 1
        assert preview["security_status"] == "scanned"
        assert "content_hash" in preview
        assert len(preview["content_hash"]) == 64  # SHA-256


class TestRatingsAndModeration:
    """Verifies factual arithmetic averages and moderation rules."""

    def test_factual_rating_calculation(self):
        # 3 ratings: 5, 4, 3 => average 4.0
        reviews = [{"rating": 5}, {"rating": 4}, {"rating": 3}]
        summary = MarketplaceRatingCalculator.calculate_summary(reviews)
        assert summary["average_rating"] == 4.0
        assert summary["total_reviews"] == 3
        assert summary["rating_distribution"][5] == 1
        assert summary["rating_distribution"][4] == 1
        assert summary["rating_distribution"][3] == 1

    def test_review_moderation_detects_credentials(self):
        review_text = "Here is my key: sk-proj-123456789012345678901234567890"
        flagged, reason = MarketplaceReviewService.moderate_review_content(review_text)
        assert flagged is True
        assert "Credential leakage" in reason

    def test_review_moderation_permits_legitimate_negative_review(self):
        review_text = "This workflow frequently fails due to timeout on large files. Needs performance improvement."
        flagged, reason = MarketplaceReviewService.moderate_review_content(review_text)
        assert flagged is False
        assert reason is None


class TestPythonSDKMarketplaceResource:
    """Verifies that Python SDK marketplace client exposes all required Step 38 methods."""

    def test_sdk_marketplace_methods_available(self):
        import sys
        if "sdk/python" not in sys.path:
            sys.path.insert(0, "sdk/python")
        from ai_work_layer import Client

        client = Client(api_key="awl_dev_mock_test_key_12345678901234567890")
        assert hasattr(client, "marketplace")
        mp = client.marketplace

        # Verify required Step 38 methods exist and are callable
        assert callable(getattr(mp, "list"))
        assert callable(getattr(mp, "get"))
        assert callable(getattr(mp, "install"))
        assert callable(getattr(mp, "update"))
        assert callable(getattr(mp, "rollback"))
        assert callable(getattr(mp, "fork"))
        assert callable(getattr(mp, "versions"))
        assert callable(getattr(mp, "list_installations"))
        assert callable(getattr(mp, "get_installation"))
        assert callable(getattr(mp, "usage"))
