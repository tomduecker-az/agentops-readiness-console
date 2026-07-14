class WorkflowCoreError(Exception):
    """Base exception for workflow core errors."""


class WorkflowNotFoundError(WorkflowCoreError):
    """Raised when a requested workflow is not registered."""


class WorkflowPacketInvalidError(WorkflowCoreError):
    """Raised when a registered workflow packet is missing or invalid."""


class DocumentNotFoundError(WorkflowCoreError):
    """Raised when a requested document is not registered or cannot be found."""


class UnsafeDocumentPathError(WorkflowCoreError):
    """Raised when a resolved document path escapes the workflow packet boundary."""