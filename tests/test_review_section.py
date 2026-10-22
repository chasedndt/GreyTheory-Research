"""Review material: the compiled conclusions beside the sources they came from.

The refusals here matter more than the happy path. A reviewer who is shown a
paraphrase without being told it is one, or content whose hash disagrees with
what it declared, is being invited to rubber-stamp - which is the single
outcome the review gate exists to prevent.
"""

from __future__ import annotations

import json

import pytest

from greytheory_app.contracts import ReadinessStatus
from greytheory_app.review_section import MAX_CONTENT_CHARS, build_review_section


class _Pattern:
    def __init__(self, value: str) -> None:
        self.type, self.value, self.note = "exact", value, ""


class _Contract:
    def __init__(self, *, human_reviewed: bool = False) -> None:
        self.human_reviewed = human_reviewed
        self.assets_in_scope = [_Pattern("gitlab.com"), _Pattern("registry.gitlab.com")]
        self.assets_out_of_scope = [_Pattern("shop.gitlab.com")]
        self.prohibited_techniques = ["denial_of_service", "social_engineering"]


class _Version:
    version = 1


class _Registry:
    def __init__(self, bundles: dict, contracts: dict | None = None) -> None:
        self._bundles = bundles
        self._contracts = contracts or {pid: _Contract() for pid in bundles}

    def programmes(self):
        return list(self._bundles)

    def current_contract(self, programme_id):
        return self._contracts.get(programme_id)

    def latest(self, programme_id):
        return _Version() if programme_id in self._bundles else None

    def source(self, programme_id, version):
        return json.dumps(self._bundles[programme_id])


def _bundle(**over):
    base = {
        "sources": [
            {
                "id": "gitlab-scope-csv",
                "capture_mode": "structured_export",
                "declared_hash": "sha256:aaa",
                "actual_hash": "sha256:aaa",
                "content": "identifier,asset_type\ngitlab.com,domain\n",
            },
            {
                "id": "gitlab-programme-guidelines",
                "capture_mode": "operator_extract",
                "declared_hash": "sha256:bbb",
                "actual_hash": "sha256:bbb",
                "content": "# Guidelines\n\n1. Do not test accounts you do not own.\n",
            },
        ],
        "human_resolutions": [],
    }
    base.update(over)
    return base


def _section(bundles=None, contracts=None):
    return build_review_section(_Registry(bundles or {"p": _bundle()}, contracts))


def _by_kind(section, kind):
    return [r for r in section.records if dict(r.attributes).get("kind") == kind]


# -- the compiled conclusions -----------------------------------------------

def test_scope_conclusions_are_shown_so_they_can_be_compared():
    section = _section()
    scope = {r.title: r for r in section.records if r.id.startswith("review:p:")}

    assert "gitlab.com" in scope["In scope"].detail
    assert "shop.gitlab.com" in scope["Out of scope"].detail
    assert "denial_of_service" in scope["Prohibited techniques"].detail


def test_an_empty_scope_list_reads_as_empty_not_as_satisfied():
    class _Bare(_Contract):
        def __init__(self):
            super().__init__()
            self.assets_out_of_scope = []

    section = _section(contracts={"p": _Bare()})
    out = next(r for r in section.records if r.title == "Out of scope")
    assert out.status is ReadinessStatus.EMPTY
    assert out.detail == "none recorded"


# -- the sources themselves --------------------------------------------------

def test_each_source_document_carries_its_content_and_capture_mode():
    docs = _by_kind(_section(), "source_document")

    assert len(docs) == 2
    csv = next(d for d in docs if d.title == "gitlab-scope-csv")
    assert "identifier,asset_type" in csv.detail
    assert dict(csv.attributes)["capture_mode"] == "structured_export"
    extract = next(d for d in docs if d.title == "gitlab-programme-guidelines")
    # A paraphrase must announce itself; reviewing one is not reviewing the source.
    assert dict(extract.attributes)["capture_mode"] == "operator_extract"


def test_a_hash_disagreement_blocks_the_document_and_the_section():
    bundle = _bundle()
    bundle["sources"][0]["actual_hash"] = "sha256:different"

    section = _section({"p": bundle})
    bad = next(d for d in _by_kind(section, "source_document") if d.title == "gitlab-scope-csv")

    assert bad.status is ReadinessStatus.BLOCKED
    assert dict(bad.attributes)["hash_agrees"] == "false"
    assert section.status is ReadinessStatus.BLOCKED
    assert dict((m.label, m.value) for m in section.metrics)["Hash disagreements"] == "1"


def test_a_missing_declared_hash_does_not_count_as_agreement():
    bundle = _bundle()
    bundle["sources"][0]["declared_hash"] = ""
    bundle["sources"][0]["actual_hash"] = ""

    doc = next(d for d in _by_kind(_section({"p": bundle}), "source_document") if d.title == "gitlab-scope-csv")
    assert dict(doc.attributes)["hash_agrees"] == "false"


def test_long_content_is_truncated_and_says_so():
    bundle = _bundle()
    bundle["sources"][0]["content"] = "x" * (MAX_CONTENT_CHARS + 500)

    doc = next(d for d in _by_kind(_section({"p": bundle}), "source_document") if d.title == "gitlab-scope-csv")
    assert len(doc.detail) == MAX_CONTENT_CHARS
    assert dict(doc.attributes)["truncated"] == "true"
    assert dict(doc.attributes)["bytes"] == str(MAX_CONTENT_CHARS + 500)


# -- what a blocked contract is waiting on -----------------------------------

def test_unresolved_human_resolutions_are_surfaced_as_blocked():
    bundle = _bundle(human_resolutions=[
        {"id": "owned-host-wildcard-vs-listed-targets", "question": "Which wins?"},
        {"id": "already-settled", "question": "Settled", "resolved_by": "chase"},
    ])

    resolutions = _by_kind(_section({"p": bundle}), "human_resolution")
    pending = next(r for r in resolutions if r.title == "owned-host-wildcard-vs-listed-targets")
    settled = next(r for r in resolutions if r.title == "already-settled")

    assert pending.status is ReadinessStatus.BLOCKED
    assert settled.status is ReadinessStatus.READY


# -- section shape -----------------------------------------------------------

def test_no_registry_is_unknown_and_no_programmes_is_empty():
    assert build_review_section(None).status is ReadinessStatus.UNKNOWN
    assert build_review_section(_Registry({})).status is ReadinessStatus.EMPTY


def test_an_unreadable_source_does_not_take_the_section_down():
    class _Broken(_Registry):
        def source(self, programme_id, version):
            raise RuntimeError("stored source is corrupt")

    section = build_review_section(_Broken({"p": _bundle()}))
    # Scope records still render; the documents simply are not there to show.
    assert section.records and not _by_kind(section, "source_document")


def test_each_programme_says_whether_it_has_been_reviewed():
    """A section-level count cannot tell a reader whether *this* programme is
    one of the ones still awaiting review."""

    section = _section(contracts={"p": _Contract(human_reviewed=False)})
    state = _by_kind(section, "programme_state")

    assert len(state) == 1
    assert dict(state[0].attributes)["human_reviewed"] == "false"
    assert state[0].status is ReadinessStatus.ATTENTION


def test_a_reviewed_programme_reads_as_reviewed():
    section = _section(contracts={"p": _Contract(human_reviewed=True)})
    state = _by_kind(section, "programme_state")[0]

    assert dict(state.attributes)["human_reviewed"] == "true"
    assert state.status is ReadinessStatus.READY


def test_a_contract_without_a_status_does_not_take_the_section_down():
    """Older stored contracts predate `status`; a missing one is reported as
    unknown rather than raising."""

    section = _section(contracts={"p": _Contract()})
    state = _by_kind(section, "programme_state")[0]

    assert dict(state.attributes)["contract_status"] == "unknown"


def test_reviewing_state_grants_no_authority():
    state = _by_kind(_section(), "programme_state")[0]
    assert dict(state.attributes)["grants_authority"] == "false"


def test_records_have_unique_ids_and_grant_nothing():
    section = _section({"a": _bundle(), "b": _bundle()})
    ids = [r.id for r in section.records]

    assert len(ids) == len(set(ids))
    for record in _by_kind(section, "in-scope"):
        assert dict(record.attributes)["grants_authority"] == "false"
