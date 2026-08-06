def verified_cookie_email(request, cookie_name):
    """Return the email carried by a legacy identity cookie (duser/ruser),
    but only if it matches the real, session-authenticated user.

    These cookies are plain, unsigned strings that a client can set to any
    value, so they must never be trusted on their own to identify "the
    current user" -- only Django's session-backed request.user is
    tamper-evident. Callers that used to read request.COOKIES[cookie_name]
    directly should use this instead.
    """
    raw = request.COOKIES.get(cookie_name)
    if not raw:
        return None

    email = raw if ':' not in raw else raw[:raw.find(':')]

    if not request.user.is_authenticated or request.user.email != email:
        return None

    return email
