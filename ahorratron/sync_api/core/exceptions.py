class LoginError(Exception):
    """Custom exception for login errors. You should not retry if this is raised."""

    pass


class RetryableError(Exception):
    """Base for errors that can be resolved by retrying the request."""

    pass


class SessionExpired(RetryableError):
    """The bank responded with a redirect (302): the session cookie is no longer
    valid and a fresh login is required before retrying."""

    pass


class InternalServerError(RetryableError):
    """The bank API responded with a 5xx error."""

    pass
