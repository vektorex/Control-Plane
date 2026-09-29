import logging
import re
import time
from typing import Any, Dict, List, Set
from urllib.parse import urlparse

from backend.app.services.evaluation.base import DeterministicEvaluator
from backend.app.services.evaluation.policies import EvaluationPolicy
from backend.app.services.evaluation.schemas import (
    CheckResult,
    CheckType,
    EvaluationContext,
    EvaluationFindingItem,
    FindingStatus,
)

logger = logging.getLogger("evaluation.citation")


class CitationEvaluator(DeterministicEvaluator):
    """
    CitationEvaluator checks whether citations and source references in the output
    faithfully match the actual retrieved documents and web sources.
    
    Prevents hallucinated/invented URLs and citations.
    Does NOT falsely require citations when no retrieval or external sources were used.
    """
    check_type = CheckType.CITATION

    URL_REGEX = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*", re.IGNORECASE)
    MARKDOWN_LINK_REGEX = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)", re.IGNORECASE)
    NUMERIC_CITATION_REGEX = re.compile(r"\[(\d+)\]")
    NAMED_CITATION_REGEX = re.compile(r"\[(?:Source|Doc|Ref|Document):\s*([^\]]+)\]", re.IGNORECASE)

    def _normalize_url(self, url: str) -> str:
        """Normalizes a URL by stripping trailing slashes and lowercasing domain."""
        try:
            parsed = urlparse(url.strip())
            netloc = parsed.netloc.lower()
            path = parsed.path.rstrip("/")
            return f"{parsed.scheme}://{netloc}{path}"
        except Exception:
            return url.strip().lower()

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url.strip())
            return parsed.netloc.lower().replace("www.", "")
        except Exception:
            return ""

    async def evaluate(
        self,
        ctx: EvaluationContext,
        policy: EvaluationPolicy,
    ) -> CheckResult:
        start_time = time.perf_counter()

        # Gather all valid retrieved sources and URLs
        retrieved_urls: Set[str] = set()
        retrieved_domains: Set[str] = set()
        retrieved_titles: Set[str] = set()
        retrieved_doc_names: Set[str] = set()
        valid_evidence_ids: List[str] = []

        for item in ctx.retrieval_sources:
            doc_name = (((item.get("document_name") if isinstance(item, dict) else getattr(item, "document_name", None)) or (item.get("title") if isinstance(item, dict) else getattr(item, "title", ""))) or "").strip().lower()
            if doc_name:
                retrieved_doc_names.add(doc_name)
            cid = str((item.get("chunk_id") if isinstance(item, dict) else getattr(item, "chunk_id", None)) or (item.get("document_id") if isinstance(item, dict) else getattr(item, "document_id", None)) or (item.get("id") if isinstance(item, dict) else getattr(item, "id", "")) or "")
            if cid:
                valid_evidence_ids.append(cid)

        for item in ctx.web_sources:
            raw_url = (item.get("url") if isinstance(item, dict) else getattr(item, "url", "")) or ""
            if raw_url:
                norm = self._normalize_url(raw_url)
                retrieved_urls.add(norm)
                dom = self._extract_domain(raw_url)
                if dom:
                    retrieved_domains.add(dom)
                valid_evidence_ids.append(raw_url)
            t = ((item.get("title") if isinstance(item, dict) else getattr(item, "title", "")) or "").strip().lower()
            if t:
                retrieved_titles.add(t)

        for item in ctx.context_items:
            meta = (item.get("metadata") if isinstance(item, dict) else getattr(item, "metadata", {})) or {}
            raw_url = (meta.get("url") if isinstance(meta, dict) else getattr(meta, "url", "")) or ""
            if raw_url:
                norm = self._normalize_url(raw_url)
                retrieved_urls.add(norm)
                dom = self._extract_domain(raw_url)
                if dom:
                    retrieved_domains.add(dom)
            t = ((item.get("title") if isinstance(item, dict) else getattr(item, "title", "")) or "").strip().lower()
            if t:
                retrieved_titles.add(t)
            cid = str((item.get("id") if isinstance(item, dict) else getattr(item, "id", "")) or "")
            if cid:
                valid_evidence_ids.append(cid)


        total_retrieved_sources = len(retrieved_urls) + len(retrieved_doc_names) + len(ctx.retrieval_sources)

        # If NO external sources or documents were retrieved:
        if total_retrieved_sources == 0:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return CheckResult(
                type=CheckType.CITATION,
                status=FindingStatus.PASSED,
                confidence=1.0,
                description="No external retrieval or web sources used. Citations not required.",
                issues=[],
                findings=[],
                metadata={"external_sources_used": False, "verified_citations_count": 0},
                duration_ms=elapsed_ms,
            )

        # Extract cited URLs and references from candidate output
        text = ctx.output_text or ""
        cited_urls = [self._normalize_url(u) for u in self.URL_REGEX.findall(text)]
        cited_links = self.MARKDOWN_LINK_REGEX.findall(text)
        numeric_citations = [int(m) for m in self.NUMERIC_CITATION_REGEX.findall(text)]
        named_citations = self.NAMED_CITATION_REGEX.findall(text)

        issues: List[str] = []
        findings: List[EvaluationFindingItem] = []
        unverified_urls: List[str] = []
        verified_count = 0

        # Check URL validity & hallucination
        for url in set(cited_urls):
            norm_url = self._normalize_url(url)
            # Check if valid URL structure
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                issues.append(f"Invalid URL structure cited: '{url}'")
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.CITATION,
                        status=FindingStatus.WARNING,
                        confidence=0.95,
                        description=f"Invalid URL syntax cited: {url}",
                        evidence_ids=[],
                        metadata={"url": url, "error": "malformed_url"},
                    )
                )
                continue

            # Check if domain or full URL matches retrieved sources
            dom = self._extract_domain(url)
            is_verified = (
                norm_url in retrieved_urls
                or url in retrieved_urls
                or any(dom and dom == r_dom for r_dom in retrieved_domains)
                or any(dom and dom in r_url for r_url in retrieved_urls)
            )

            if is_verified:
                verified_count += 1
            else:
                unverified_urls.append(url)
                issues.append(f"Cited URL was not found in retrieved sources: '{url}'")
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.CITATION,
                        status=FindingStatus.FAILED if policy.strict_mode else FindingStatus.WARNING,
                        confidence=0.9,
                        description=f"Output cited unretrieved URL: {url}",
                        evidence_ids=[],
                        metadata={"unretrieved_url": url},
                    )
                )

        # Check markdown links (e.g. [Title](doc_id) or [Title](url))
        for text_label, target in cited_links:
            target_clean = target.strip()
            if target_clean.startswith("http://") or target_clean.startswith("https://"):
                continue  # already checked in cited_urls
            if target_clean in valid_evidence_ids or any(target_clean.lower() in str(eid).lower() for eid in valid_evidence_ids):
                verified_count += 1
            else:
                issues.append(f"Cited evidence ID '{target_clean}' does not match any retrieved source.")
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.CITATION,
                        status=FindingStatus.WARNING,
                        confidence=0.9,
                        description=f"Unrecognized evidence reference '{target_clean}'.",
                        evidence_ids=valid_evidence_ids,
                    )
                )


        # Check numeric citation indices (e.g. [1], [2] within bounds of retrieved sources)
        for num in numeric_citations:
            if num < 1 or num > len(valid_evidence_ids):
                issues.append(f"Citation index [{num}] out of bounds (retrieved {len(valid_evidence_ids)} sources).")
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.CITATION,
                        status=FindingStatus.WARNING,
                        confidence=0.95,
                        description=f"Citation reference [{num}] exceeds retrieved evidence count.",
                        evidence_ids=valid_evidence_ids,
                        metadata={"out_of_bounds_index": num},
                    )
                )
            else:
                verified_count += 1

        # Check citation coverage when external retrieval was actively used
        has_citations = bool(cited_urls or cited_links or numeric_citations or named_citations)
        if not has_citations and policy.require_citation_if_sources and total_retrieved_sources > 0:
            # Output did not include source citations
            issues.append("Response does not include inline citations or source references for retrieved information.")
            findings.append(
                EvaluationFindingItem(
                    check_type=CheckType.CITATION,
                    status=FindingStatus.WARNING,
                    confidence=0.8,
                    description="Retrieved sources were used in task execution, but response does not contain explicit citations.",
                    evidence_ids=valid_evidence_ids,
                    metadata={"missing_citations": True},
                )
            )

        # Determine overall check status
        has_failed = any(f.status == FindingStatus.FAILED for f in findings)
        has_warning = any(f.status == FindingStatus.WARNING for f in findings) or bool(issues)

        if has_failed or (has_warning and policy.strict_mode and unverified_urls):
            overall_status = FindingStatus.FAILED
        elif has_warning:
            overall_status = FindingStatus.WARNING
        else:
            overall_status = FindingStatus.PASSED

        desc = (
            f"Verified {verified_count} source citations against retrieved evidence."
            if overall_status == FindingStatus.PASSED
            else f"Found {len(issues)} citation / source reference issue(s)."
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return CheckResult(
            type=CheckType.CITATION,
            status=overall_status,
            confidence=0.95,
            description=desc,
            issues=issues,
            findings=findings,
            metadata={
                "retrieved_sources_count": total_retrieved_sources,
                "verified_citations_count": verified_count,
                "unverified_urls": unverified_urls,
            },
            duration_ms=elapsed_ms,
        )
