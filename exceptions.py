class NotFoundError(Exception):
    """Raised when a requested resource is not found."""

    pass


class DuplicateResourceError(Exception):
    """Raised when attempting to create a resource that already exists."""

    pass


class MismatchedDataError(Exception):
    """Raised when provided data does not match expected values (e.g., SKU in update request)."""

    pass


class InvalidStateTransitionError(Exception):
    """Raised when an operation would result in an invalid state transition (e.g., cancelled order set to shipped)."""

    pass


class DependencyConflictError(Exception):
    """Raised when an operation cannot be performed due to existing dependencies (e.g., deleting a product that has associated orders)."""

    pass


class ContractTimeError(Exception):
    """Raised when a contract timeline is invalid."""

    pass
