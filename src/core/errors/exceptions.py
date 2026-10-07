"""Custom domain exceptions for LinkedIn Agent Suite."""

class LinkedInAgentError(Exception):
    """Base exception for all suite errors."""
    pass

class ConfigurationError(LinkedInAgentError):
    """Raised when configuration is invalid or missing."""
    pass

class AuthenticationError(LinkedInAgentError):
    """Raised when authentication is expired, invalid, or required."""
    pass

class SecurityCheckpointError(AuthenticationError):
    """Raised when LinkedIn presents a CAPTCHA, PIN, or verification checkpoint."""
    pass

class ApprovalRequiredError(LinkedInAgentError):
    """Raised when an unapproved write action is attempted."""
    pass

class RateLimitError(LinkedInAgentError):
    """Raised when LinkedIn rate limits are encountered."""
    pass

class BrowserError(LinkedInAgentError):
    """Raised when browser automation fails or crashes."""
    pass

class ContentValidationError(LinkedInAgentError):
    """Raised when generated content fails factual or quality checks."""
    pass
