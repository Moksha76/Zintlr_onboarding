import os

import msal

import config

_app = None
_cache = None


class GraphNotConfigured(Exception):
    pass


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(config.GRAPH_TOKEN_CACHE_PATH):
        with open(config.GRAPH_TOKEN_CACHE_PATH, "r") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache():
    if _cache is not None and _cache.has_state_changed:
        with open(config.GRAPH_TOKEN_CACHE_PATH, "w") as f:
            f.write(_cache.serialize())


def _get_app() -> msal.PublicClientApplication:
    global _app, _cache
    if not config.GRAPH_CLIENT_ID or not config.GRAPH_TENANT_ID:
        raise GraphNotConfigured("GRAPH_CLIENT_ID / GRAPH_TENANT_ID not set in .env yet.")
    if _app is None:
        _cache = _load_cache()
        _app = msal.PublicClientApplication(
            client_id=config.GRAPH_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{config.GRAPH_TENANT_ID}",
            token_cache=_cache,
        )
    return _app


def get_connected_account() -> str | None:
    """Returns the signed-in account's username (email), or None if not connected
    (also None on any Graph/network error — never raises, since this gets called
    on every Dashboard render)."""
    try:
        app = _get_app()
        accounts = app.get_accounts()
        return accounts[0]["username"] if accounts else None
    except Exception:
        return None


def get_access_token_silent() -> str | None:
    """Try to get a token from the cached signed-in account, refreshing if needed.
    Returns None if there's no connected account or anything goes wrong — callers
    should fall back to prompting a (re)connect via the device flow."""
    try:
        app = _get_app()
        accounts = app.get_accounts()
        if not accounts:
            return None
        result = app.acquire_token_silent(config.GRAPH_SCOPES, account=accounts[0])
        _save_cache()
        if result and "access_token" in result:
            return result["access_token"]
        return None
    except Exception:
        return None


def start_device_flow() -> dict:
    """Kick off sign-in. Returns the MSAL flow dict (contains user_code,
    verification_uri, message) — show `message` to the user, then repeatedly
    call poll_device_flow(flow) until it reports success or failure."""
    app = _get_app()
    flow = app.initiate_device_flow(scopes=config.GRAPH_SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Failed to start device flow: {flow.get('error_description', flow)}")
    return flow


def poll_device_flow(flow: dict) -> dict:
    """Do a single non-blocking check of whether the user has finished signing
    in yet — call this again (e.g. from a "Check now" button) until it reports
    success or failure. Returns {"status": "pending"|"success"|"error", ...}."""
    try:
        app = _get_app()
        result = app.acquire_token_by_device_flow(flow, exit_condition=lambda f: True)

        if "access_token" in result:
            _save_cache()
            accounts = app.get_accounts()
            username = accounts[0]["username"] if accounts else None
            return {"status": "success", "username": username}

        error = result.get("error")
        if error in (None, "authorization_pending", "slow_down"):
            return {"status": "pending"}

        return {"status": "error", "detail": result.get("error_description", error)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def disconnect():
    """Remove the cached account so the app forgets it's signed in."""
    global _app, _cache
    try:
        app = _get_app()
        for account in app.get_accounts():
            app.remove_account(account)
        _save_cache()
    except Exception:
        pass
    if os.path.exists(config.GRAPH_TOKEN_CACHE_PATH):
        os.remove(config.GRAPH_TOKEN_CACHE_PATH)
    _app = None
    _cache = None
