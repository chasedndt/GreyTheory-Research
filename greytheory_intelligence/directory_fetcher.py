"""Bounded public-directory reads, authorised by ADR-0029 tier 1.

This is the first component in GreyTheory permitted to open an outbound
connection, so every limit it must respect is enforced here rather than assumed
of the caller:

* HTTPS only, to an origin declared in the provider registry;
* the provider must carry ``PROGRAMME_AUTHORITY`` trust — an unlisted or
  lesser-trusted host is refused, never fetched cautiously;
* no credentials, no cookies, no authentication header of any kind;
* redirects are refused rather than followed, so a redirect cannot walk the
  read off the approved origin;
* a hard response ceiling, an overall deadline, and a content-type check;
* GET only.

What this module deliberately cannot do: reach a programme's assets, send a
credential, submit anything, or grant testing authority. Retrieved content is
``PUBLIC`` and ``UNTRUSTED`` source evidence for curriculum selection.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import http.client
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlsplit

from greytheory_intelligence.authorisation import (
    IntelligenceAuthorisationError,
    ReadTier,
    authorise,
)
from greytheory_intelligence.registry import IntelligencePlan


ALLOWED_CONTENT_TYPES = ("application/json", "text/html", "text/plain")
DEFAULT_TIMEOUT_SECONDS = 20.0


class DirectoryFetchError(RuntimeError):
    """Raised when a read cannot be performed inside its declared bounds."""


@dataclass(frozen=True)
class DirectoryEvidence:
    """Immutable record of one bounded public read."""

    provider_id: str
    identifier: str
    url: str
    status: int
    content_type: str
    body_sha256: str
    body_bytes: int
    retrieved_at: str
    data_class: str = "PUBLIC"
    trust: str = "UNTRUSTED"
    credentials_sent: bool = False
    redirects_followed: int = 0
    target_interaction: bool = False
    grants_authority: bool = False
    body: bytes = field(default=b"", repr=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "greytheory.directory-evidence/1",
            "provider_id": self.provider_id,
            "identifier": self.identifier,
            "url": self.url,
            "status": self.status,
            "content_type": self.content_type,
            "body_sha256": self.body_sha256,
            "body_bytes": self.body_bytes,
            "retrieved_at": self.retrieved_at,
            "data_class": self.data_class,
            "trust": self.trust,
            "credentials_sent": self.credentials_sent,
            "redirects_followed": self.redirects_followed,
            "target_interaction": self.target_interaction,
            "grants_authority": self.grants_authority,
        }


def _require_authorised_provider(plan: IntelligencePlan):
    """Delegate to the shared tier authorisation, as ADR-0029 requires."""

    try:
        return authorise(plan, tier=ReadTier.PUBLIC_DIRECTORY)
    except IntelligenceAuthorisationError as error:
        raise DirectoryFetchError(str(error)) from error


def build_directory_url(plan: IntelligencePlan) -> str:
    """Return the exact URL a plan authorises, without fetching it."""

    provider = _require_authorised_provider(plan)
    platform, _, handle = plan.identifier.partition(":")
    if not handle:
        raise DirectoryFetchError("directory identifier needs a programme handle")
    if not provider.id.startswith(platform):
        raise DirectoryFetchError("identifier platform does not match the provider")
    return f"{provider.origin.rstrip('/')}/{handle}"


def fetch_directory(
    plan: IntelligencePlan,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    connection_factory=None,
) -> DirectoryEvidence:
    """Perform one bounded, unauthenticated public read for ``plan``."""

    provider = _require_authorised_provider(plan)
    url = build_directory_url(plan)
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise DirectoryFetchError("directory reads require HTTPS")

    if connection_factory is None:
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        connection = http.client.HTTPSConnection(
            parts.hostname, parts.port or 443, timeout=timeout_seconds, context=context
        )
    else:
        connection = connection_factory(parts.hostname, parts.port or 443, timeout_seconds)

    try:
        path = parts.path or "/"
        # No cookie, no authorization header, no api key: tier 1 is anonymous.
        connection.request("GET", path, headers={
            "Host": parts.hostname,
            "Accept": "application/json, text/html;q=0.8",
            "User-Agent": "GreyTheory-directory-reader/1 (+local research learner)",
            "Connection": "close",
        })
        response = connection.getresponse()
        status = int(response.status)

        # A redirect could walk the read off the approved origin, so refuse it.
        if 300 <= status < 400:
            raise DirectoryFetchError(
                f"refusing to follow a redirect from {provider.name}"
            )
        if status != 200:
            raise DirectoryFetchError(f"{provider.name} returned status {status}")

        content_type = (response.getheader("Content-Type") or "").split(";")[0].strip().lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise DirectoryFetchError(f"unexpected content type {content_type!r}")

        ceiling = provider.maximum_response_bytes
        body = response.read(ceiling + 1)
        if len(body) > ceiling:
            raise DirectoryFetchError("response exceeded the declared ceiling")
    finally:
        connection.close()

    return DirectoryEvidence(
        provider_id=provider.id,
        identifier=plan.identifier,
        url=url,
        status=status,
        content_type=content_type,
        body_sha256=hashlib.sha256(body).hexdigest(),
        body_bytes=len(body),
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        body=body,
    )
