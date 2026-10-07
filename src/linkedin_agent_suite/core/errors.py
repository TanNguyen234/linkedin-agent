"""Unified Exception hierarchy for LinkedIn Agent Suite."""


class LinkedInAgentError(Exception):
    """Base exception for all suite errors."""


class ConfigurationError(LinkedInAgentError):
    """Raised when configuration is missing or invalid."""


class AuthenticationError(LinkedInAgentError):
    """Raised when user is not logged in or token is invalid."""


class CheckpointChallengeError(AuthenticationError):
    """Raised when LinkedIn presents a security challenge, captcha, or PIN."""


class AccountRestrictedError(AuthenticationError):
    """Raised when LinkedIn account has active restriction or ban."""


class BrowserError(LinkedInAgentError):
    """Base exception for browser automation failures."""


class BrowserBusyError(BrowserError):
    """Raised when the browser profile is locked by another process."""


class NavigationTimeoutError(BrowserError):
    """Raised when navigating to a LinkedIn page times out."""


class ApprovalRequiredError(LinkedInAgentError):
    """Raised when an irreversible write action lacks explicit valid confirmation."""


class RateLimitDetectedError(LinkedInAgentError):
    """Raised when LinkedIn rate limiting is detected."""


class ProfileNotFoundError(LinkedInAgentError):
    """Raised when a requested profile does not exist or is private."""


class JobNotFoundError(LinkedInAgentError):
    """Raised when a job posting cannot be found."""


class ContentValidationError(LinkedInAgentError):
    """Raised when generated content fails factual or quality checks."""
