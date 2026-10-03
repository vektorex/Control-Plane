"""
Constants and Enums for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
"""
from enum import Enum


# Safety limits (infrastructure safety limits, not hardcoded billing)
ORGANIZATION_MAX_MEMBERS = 50
WORKSPACE_MAX_MEMBERS = 50
PROJECT_MAX_MEMBERS = 50
ORGANIZATION_MAX_WORKSPACES = 20

# Invitation expiration duration
INVITATION_EXPIRATION_DAYS = 7


class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class MemberStatus(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REMOVED = "removed"


class OrganizationRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class WorkspaceRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectRole(str, Enum):
    EDITOR = "editor"
    VIEWER = "viewer"


class ProjectAccessMode(str, Enum):
    WORKSPACE = "workspace"
    RESTRICTED = "restricted"


class AccessControlAuditEvent(str, Enum):
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_ARCHIVED = "organization.archived"

    MEMBER_INVITED = "member.invited"
    MEMBER_JOINED = "member.joined"
    MEMBER_ROLE_CHANGED = "member.role_changed"
    MEMBER_SUSPENDED = "member.suspended"
    MEMBER_REMOVED = "member.removed"

    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_ARCHIVED = "workspace.archived"

    WORKSPACE_MEMBER_ADDED = "workspace.member_added"
    WORKSPACE_MEMBER_UPDATED = "workspace.member_updated"
    WORKSPACE_MEMBER_REMOVED = "workspace.member_removed"

    PROJECT_MEMBER_ADDED = "project.member_added"
    PROJECT_MEMBER_UPDATED = "project.member_updated"
    PROJECT_MEMBER_REMOVED = "project.member_removed"
    PROJECT_ACCESS_CHANGED = "project.access_changed"

    OWNERSHIP_TRANSFERRED = "ownership.transferred"
