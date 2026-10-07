"""Exception hierarchy for LinkedIn Agent Suite."""


class LinkedInAgentError(Exception):
    """Base exception for all LinkedIn Agent Suite errors."""


class ConfigurationError(LinkedInAgentError):
    """Raised when configuration is missing or invalid."""


class AuthenticationError(LinkedInAgentError):
    """Raised when user is not logged into LinkedIn."""


class CheckpointChallengeError(AuthenticationError):
    """Raised when LinkedIn presents a security challenge or CAPTCHA."""


class AccountRestrictedError(AuthenticationError):
    """Raised when LinkedIn account is restricted."""


class BrowserError(LinkedInAgentError):
    """Base exception for browser automation failures."""


class BrowserBusyError(BrowserError):
    """Raised when the browser profile is locked by another process."""


class NavigationTimeoutError(BrowserError):
    """Raised when navigating to a LinkedIn page times out."""


class ActionConfirmationRequiredError(LinkedInAgentError):
    """Raised when an irreversible write action lacks explicit confirmation."""


class RateLimitDetectedError(LinkedInAgentError):
    """Raised when LinkedIn throttle or rate-limiting behavior is encountered."""


class ProfileNotFoundError(LinkedInAgentError):
    """Raised when a requested profile does not exist or is private."""


class JobNotFoundError(LinkedInAgentError):
    """Raised when a job posting cannot be found or has expired."""
