"""
Errors for Step 45: Control Tower.
"""


class ControlTowerError(Exception):
    pass


class ViewNotFoundError(ControlTowerError):
    pass


class ViewPermissionError(ControlTowerError):
    pass


class AttentionNotFoundError(ControlTowerError):
    pass


class WorkstreamNotFoundError(ControlTowerError):
    pass


class SearchPermissionError(ControlTowerError):
    pass


class BriefingUnavailableError(ControlTowerError):
    """Raised when AI briefing is unavailable. Control Tower still functions normally."""
    pass


class CrossTenantAccessError(ControlTowerError):
    """Raised on cross-tenant access attempts."""
    pass
