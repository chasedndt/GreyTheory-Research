"""Strict, network-free URL and address policy for the passive broker."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


CONTROL_OR_SPACE = re.compile(r"[\x00-\x20\x7f]")
AMBIGUOUS_ESCAPES = re.compile(r"%(?:00|2e|2f|3f|5c)", re.IGNORECASE)


class TargetPolicyError(ValueError):
    """Raised when a target cannot be represented without ambiguity."""


def canonical_https_url(value: str) -> str:
    """Return the one accepted spelling of an unauthenticated HTTPS URL.

    The first passive action is deliberately narrower than a browser: HTTPS on
    port 443, no userinfo, query, fragment, IP literal, ambiguous escape, or
    path normalisation. The Gate must evaluate this exact canonical string.
    """

    raw = str(value or "")
    if raw != raw.strip() or not raw or CONTROL_OR_SPACE.search(raw):
        raise TargetPolicyError("target URL contains whitespace or control bytes")
    if "\\" in raw or AMBIGUOUS_ESCAPES.search(raw):
        raise TargetPolicyError("target URL contains an ambiguous path spelling")
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise TargetPolicyError(f"target URL is malformed: {exc}") from exc
    if parsed.scheme.lower() != "https":
        raise TargetPolicyError("the passive pilot accepts HTTPS only")
    if parsed.username is not None or parsed.password is not None:
        raise TargetPolicyError("target URL cannot contain user information")
    if not parsed.hostname:
        raise TargetPolicyError("target URL requires a hostname")
    if parsed.query or parsed.fragment:
        raise TargetPolicyError("the first passive action refuses query and fragment data")
    if port not in (None, 443):
        raise TargetPolicyError("the passive pilot accepts port 443 only")

    hostname = parsed.hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise TargetPolicyError("the passive pilot requires a DNS hostname, not an IP literal")
    try:
        ascii_host = hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise TargetPolicyError("target hostname is not valid IDNA") from exc
    if not ascii_host or len(ascii_host) > 253:
        raise TargetPolicyError("target hostname length is invalid")
    labels = ascii_host.split(".")
    if len(labels) < 2 or any(
        not label
        or len(label) > 63
        or label.startswith("-")
        or label.endswith("-")
        or not re.fullmatch(r"[a-z0-9-]+", label)
        for label in labels
    ):
        raise TargetPolicyError("target hostname is not a canonical public DNS name")

    path = parsed.path or "/"
    segments = path.split("/")
    if any(segment in {".", ".."} for segment in segments) or not path.startswith("/"):
        raise TargetPolicyError("target path must already be absolute and normalised")
    canonical = urlunsplit(("https", ascii_host, path, "", ""))
    if canonical != raw:
        raise TargetPolicyError(
            f"target URL is not canonical; use the exact form {canonical!r}"
        )
    return canonical


def canonical_hostname(url: str) -> str:
    return urlsplit(canonical_https_url(url)).hostname or ""


def public_addresses(values: tuple[str, ...]) -> tuple[str, ...]:
    """Validate a complete DNS answer and return canonical sorted addresses."""

    if not values:
        raise TargetPolicyError("DNS resolution returned no addresses")
    result: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or "%" in text:
            raise TargetPolicyError("resolved address is empty or zone-qualified")
        try:
            address = ipaddress.ip_address(text)
        except ValueError as exc:
            raise TargetPolicyError(f"resolved address {text!r} is invalid") from exc
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            if not address.ipv4_mapped.is_global:
                raise TargetPolicyError(
                    f"resolved address {address} maps to a non-public IPv4 address"
                )
        if not address.is_global:
            raise TargetPolicyError(
                f"resolved address {address} is private, local, reserved, or non-global"
            )
        result.add(address.compressed)
    return tuple(sorted(result))


__all__ = [
    "TargetPolicyError",
    "canonical_hostname",
    "canonical_https_url",
    "public_addresses",
]
