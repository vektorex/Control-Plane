class CoordinationError(Exception): pass
class DependencyCycleError(CoordinationError): pass
class BlockingConflictError(CoordinationError): pass
