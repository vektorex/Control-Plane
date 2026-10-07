class ReleaseError(Exception):
    pass
class AuthorizationError(ReleaseError):
    pass
class PreconditionError(ReleaseError):
    pass
class VerificationError(ReleaseError):
    pass\n