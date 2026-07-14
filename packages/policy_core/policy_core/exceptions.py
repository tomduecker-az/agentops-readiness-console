class PolicyCoreError(Exception):
    """Base exception for policy core errors."""


class UnknownDataElementError(PolicyCoreError):
    """Raised when a requested data element is not known to the policy catalog."""


class UnknownToolError(PolicyCoreError):
    """Raised when a requested tool is not known to the policy catalog."""


class UnauthorizedToolAccessError(PolicyCoreError):
    """Raised when an actor or agent is not allowed to use a tool."""