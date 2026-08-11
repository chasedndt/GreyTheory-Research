"""Scope Watch: a source that cannot be read is never reported as unchanged."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from greytheory.audit import AuditLog
from greytheory.scopewatch import (
    LocalSourceFetcher,
    ScopeWatch,
    SourceState,
    WatchError,
    WatchedSource,
    digest,
    sources_from_bundle,
)

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def sources(tmp_path):
    root = tmp_path / "sources"
    root.mkdir()
    (root / "policy.md").write_text("Scope: *.example.test", encoding="utf-8")
    (root / "platform.md").write_text("Platform defaults v1", encoding="utf-8")
    return root


def watched(root: Path, name: str) -> WatchedSource:
    return WatchedSource(
        source_id=name,
        locator=name,
        recorded_hash=digest((root / name).read_bytes()),
        kind="programme_policy",
    )


def watcher(root: Path, **kw) -> ScopeWatch:
    return ScopeWatch(LocalSourceFetcher(root), clock=lambda: NOW, **kw)


class TestFetcherBoundary:
    def test_the_local_fetcher_declares_no_network(self):
        assert LocalSourceFetcher.network is False

    def test_a_network_fetcher_is_refused_by_default(self, sources):
        class HttpFetcher:
            fetcher_id = "http"
            network = True

            def fetch(self, locator):  # pragma: no cover - must not run
                raise AssertionError("should never be called")

        with pytest.raises(WatchError, match="raise the operating posture"):
            ScopeWatch(HttpFetcher())

    def test_a_network_fetcher_can_be_enabled_deliberately(self, sources):
        class HttpFetcher:
            fetcher_id = "http"
            network = True

            def fetch(self, locator):
                return b"fetched"

        watch = ScopeWatch(HttpFetcher(), allow_network_fetcher=True, clock=lambda: NOW)
        result = watch.check("acme", [WatchedSource("s1", "x", digest(b"fetched"))])
        assert result.observations[0].state is SourceState.UNCHANGED

    def test_the_fetcher_cannot_read_outside_its_root(self, sources, tmp_path):
        (tmp_path / "secret.md").write_text("private", encoding="utf-8")
        with pytest.raises(WatchError, match="outside the source root"):
            LocalSourceFetcher(sources).fetch("../secret.md")

    def test_a_missing_root_is_an_error(self, tmp_path):
        with pytest.raises(WatchError, match="not a directory"):
            LocalSourceFetcher(tmp_path / "nope")


class TestDetection:
    def test_unchanged_sources_are_quiet(self, sources):
        result = watcher(sources).check(
            "acme", [watched(sources, "policy.md"), watched(sources, "platform.md")]
        )
        assert result.needs_attention == []
        assert not result.review_invalidated

    def test_a_changed_source_invalidates_the_review(self, sources):
        recorded = [watched(sources, "policy.md")]
        (sources / "policy.md").write_text("Scope: nothing at all", encoding="utf-8")
        result = watcher(sources).check("acme", recorded)

        assert result.changed[0].source_id == "policy.md"
        assert result.review_invalidated
        assert "changed since capture" in " ".join(result.summary())

    def test_a_removed_source_is_gone_and_invalidates_review(self, sources):
        recorded = [watched(sources, "policy.md")]
        (sources / "policy.md").unlink()
        result = watcher(sources).check("acme", recorded)

        assert result.gone[0].source_id == "policy.md"
        assert result.review_invalidated

    def test_an_unreadable_source_is_unreachable_not_unchanged(self, sources):
        # The distinction that matters: a source nobody could check has not
        # been shown to be the same.
        class BrokenFetcher:
            fetcher_id = "broken"
            network = False

            def fetch(self, locator):
                raise PermissionError("locked")

        watch = ScopeWatch(BrokenFetcher(), clock=lambda: NOW)
        result = watch.check("acme", [WatchedSource("s1", "x", "abc")])
        observation = result.observations[0]

        assert observation.state is SourceState.UNREACHABLE
        assert observation.state is not SourceState.UNCHANGED
        assert observation.needs_attention
        assert "PermissionError" in observation.error

    def test_an_unreachable_source_does_not_by_itself_invalidate_review(self, sources):
        # It needs attention, but "could not read it" is not "it changed", and
        # claiming otherwise would make every network blip look like drift.
        class BrokenFetcher:
            fetcher_id = "broken"
            network = False

            def fetch(self, locator):
                raise TimeoutError("slow")

        result = ScopeWatch(BrokenFetcher(), clock=lambda: NOW).check(
            "acme", [WatchedSource("s1", "x", "abc")]
        )
        assert not result.review_invalidated
        assert result.unreachable

    def test_new_sources_are_reported_when_the_origin_can_enumerate(self, sources):
        result = watcher(sources).check(
            "acme",
            [watched(sources, "policy.md")],
            observed_ids=["policy.md", "appendix.md"],
        )
        new = [o for o in result.observations if o.state is SourceState.NEW]
        assert [o.source_id for o in new] == ["appendix.md"]

    def test_watching_nothing_is_an_error(self, sources):
        with pytest.raises(WatchError, match="no recorded sources"):
            watcher(sources).check("acme", [])


class TestNoPermission:
    def test_a_watch_result_carries_no_authority(self, sources):
        result = watcher(sources).check("acme", [watched(sources, "policy.md")])
        # Nothing on the result grants anything; it reports and stops.
        assert not hasattr(result, "contract")
        assert not hasattr(result, "verified")
        assert set(result.to_dict()) == {
            "programme_id",
            "checked_at",
            "fetcher_id",
            "review_invalidated",
            "summary",
            "observations",
        }


class TestAuditing:
    def test_runs_are_recorded(self, sources, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        watcher(sources, audit=audit).check("acme", [watched(sources, "policy.md")])
        record = audit.records()[-1]
        assert record.action == "scopewatch.check"
        assert record.detail["programme_id"] == "acme"
        assert record.detail["network_fetcher"] is False
        audit.verify()

    def test_the_record_says_whether_review_was_invalidated(self, sources, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        recorded = [watched(sources, "policy.md")]
        (sources / "policy.md").write_text("different", encoding="utf-8")
        watcher(sources, audit=audit).check("acme", recorded)
        assert audit.records()[-1].detail["review_invalidated"] is True


class TestBundleExtraction:
    def test_reads_the_registry_bundle_shape(self):
        watched_sources = sources_from_bundle(
            {
                "sources": [
                    {
                        "source_id": "policy",
                        "local_path": "policy.md",
                        "hash": "sha256:" + "a" * 64,
                        "kind": "programme_policy",
                    }
                ]
            }
        )
        assert watched_sources[0].recorded_hash == "a" * 64
        assert watched_sources[0].kind == "programme_policy"

    def test_a_source_without_a_hash_is_skipped_not_guessed(self):
        # Watching something we cannot compare against would report every run
        # as changed.
        assert sources_from_bundle(
            {"sources": [{"source_id": "policy", "local_path": "policy.md"}]}
        ) == []

    def test_a_bundle_with_no_sources_yields_nothing(self):
        assert sources_from_bundle({}) == []
