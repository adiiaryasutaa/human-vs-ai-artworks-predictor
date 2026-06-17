"""Fetch an image from a user-supplied URL with SSRF protections.

Guards applied:
- only http/https schemes
- every resolved IP for the host must be public (no loopback, private,
  link-local, reserved, or multicast ranges)
- redirects are re-validated with the same rules
- response size is capped and the request times out

Note: validation resolves DNS separately from the actual request, so a
malicious DNS server could in theory swap records between the two lookups
(DNS rebinding). Acceptable risk for a local single-user tool.
"""

import io
import ipaddress
import socket
import urllib.request
from urllib.parse import urlparse

MAX_BYTES = 15 * 1024 * 1024
TIMEOUT_SECONDS = 15
USER_AGENT = "human-vs-ai-art-detector/1.0"


class UrlFetchError(Exception):
    """User-presentable fetch failure."""


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UrlFetchError("URL must start with http:// or https://.")
    if not parsed.hostname:
        raise UrlFetchError("URL has no host.")

    try:
        addrinfo = socket.getaddrinfo(parsed.hostname, parsed.port or 0, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise UrlFetchError("Could not resolve that host.")

    for family, _, _, _, sockaddr in addrinfo:
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global:
            raise UrlFetchError("URL points to a private or local address, which is not allowed.")


class _ValidatingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_image_bytes(url: str) -> io.BytesIO:
    """Download an image from `url` and return its bytes, enforcing SSRF guards."""
    url = url.strip()
    _validate_url(url)

    opener = urllib.request.build_opener(_ValidatingRedirectHandler())
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            data = response.read(MAX_BYTES + 1)
    except UrlFetchError:
        raise
    except Exception:
        raise UrlFetchError("Could not download an image from that URL.")

    if len(data) > MAX_BYTES:
        raise UrlFetchError("That file is too large (over 15 MB).")
    if not data:
        raise UrlFetchError("That URL returned no data.")

    return io.BytesIO(data)
