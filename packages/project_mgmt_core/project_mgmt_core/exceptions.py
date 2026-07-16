class ProjectMgmtCoreError(Exception):
    """Base exception for project management core errors."""


class ApprovalRequiredError(ProjectMgmtCoreError):
    """Raised when a write action is attempted without approval."""


class ProjectMgmtConfigurationError(ProjectMgmtCoreError):
    """Raised when required GitHub configuration is missing."""


class IssueCreationError(ProjectMgmtCoreError):
    """Raised when GitHub issue creation fails."""