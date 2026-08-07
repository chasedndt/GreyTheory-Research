"""Advisory sets: real data, right ecosystem, right version ordering."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json

import pytest

from greytheory.advisories import (
    Advisory,
    AdvisorySet,
    Version,
    from_osv,
    normalise_ecosystem,
    normalise_package,
)

OSV_RECORD = {
    "id": "GHSA-fixture-0001",
    "aliases": ["CVE-2026-00001"],
    "summary": "Fictional flaw in a fictional package.",
    "severity": [{"type": "CVSS_V3", "score": "7.5"}],
    "affected": [
        {
            "package": {"ecosystem": "PyPI", "name": "example_lib"},
            "ranges": [
                {
                    "type": "ECOSYSTEM",
                    "events": [{"introduced": "1.0.0"}, {"fixed": "1.3.0"}],
                }
            ],
        }
    ],
}


class TestVersionOrdering:
    def test_numeric_components_compare_numerically(self):
        # String comparison would put 10 before 9.
        assert Version("1.9.0") < Version("1.10.0")
        assert Version("2.0.0") > Version("1.99.99")

    def test_missing_components_are_zero(self):
        assert Version("1.2") == Version("1.2.0")
        assert Version("1.2") < Version("1.2.1")

    def test_a_prerelease_sorts_before_its_release(self):
        # Getting this backwards reports a release candidate as patched.
        assert Version("2.0.0-rc1") < Version("2.0.0")
        assert Version("2.0.0rc1") < Version("2.0.0")
        assert Version("1.0b2") < Version("1.0")

    def test_prereleases_order_among_themselves(self):
        assert Version("2.0.0-rc1") < Version("2.0.0-rc2")

    def test_build_metadata_is_ignored_for_ordering(self):
        assert Version("1.2.3+build7") == Version("1.2.3")

    def test_unparseable_versions_do_not_explode(self):
        assert Version("weird").release == (0,)


class TestNormalisation:
    def test_ecosystem_aliases(self):
        assert normalise_ecosystem("pypi") == "PyPI"
        assert normalise_ecosystem("Python") == "PyPI"
        assert normalise_ecosystem("node") == "npm"

    def test_unknown_ecosystems_pass_through(self):
        assert normalise_ecosystem("Hex") == "Hex"

    def test_pypi_names_normalise_per_pep503(self):
        assert normalise_package("Example_Lib", "PyPI") == "example-lib"
        assert normalise_package("example.lib", "PyPI") == "example-lib"

    def test_npm_names_are_only_lowercased(self):
        assert normalise_package("Some_Pkg", "npm") == "some_pkg"


class TestAdvisoryRanges:
    def advisory(self, **kw) -> Advisory:
        base = dict(
            id="A", package="p", ecosystem="PyPI", introduced="1.0.0", fixed="1.3.0"
        )
        base.update(kw)
        return Advisory(**base)

    def test_introduced_is_inclusive(self):
        assert self.advisory().affects("1.0.0")

    def test_fixed_is_exclusive(self):
        # Reporting the patched release as vulnerable is the classic error.
        assert not self.advisory().affects("1.3.0")
        assert self.advisory().affects("1.2.9")

    def test_below_introduced_does_not_match(self):
        assert not self.advisory().affects("0.9.0")

    def test_an_open_upper_bound_matches_everything_above(self):
        assert self.advisory(fixed=None).affects("99.0.0")

    def test_an_open_lower_bound_matches_everything_below_the_fix(self):
        assert self.advisory(introduced=None).affects("0.0.1")


class TestOsvImport:
    def test_converts_a_record(self):
        advisories = from_osv(OSV_RECORD)
        assert len(advisories) == 1
        advisory = advisories[0]
        assert advisory.id == "GHSA-fixture-0001"
        assert advisory.package == "example-lib"  # PEP 503 normalised
        assert advisory.ecosystem == "PyPI"
        assert advisory.introduced == "1.0.0"
        assert advisory.fixed == "1.3.0"
        assert "CVE-2026-00001" in advisory.aliases
        assert advisory.severity == "7.5"

    def test_introduced_zero_becomes_an_open_lower_bound(self):
        record = json.loads(json.dumps(OSV_RECORD))
        record["affected"][0]["ranges"][0]["events"] = [
            {"introduced": "0"},
            {"fixed": "2.0.0"},
        ]
        assert from_osv(record)[0].introduced is None

    def test_a_record_with_no_usable_range_is_skipped(self):
        # An advisory with unknown bounds would match every version.
        record = json.loads(json.dumps(OSV_RECORD))
        record["affected"][0]["ranges"] = []
        assert from_osv(record) == []

    def test_multiple_affected_packages_become_multiple_advisories(self):
        record = json.loads(json.dumps(OSV_RECORD))
        record["affected"].append(
            {
                "package": {"ecosystem": "npm", "name": "example-lib"},
                "ranges": [
                    {"events": [{"introduced": "1.0.0"}, {"fixed": "1.1.0"}]}
                ],
            }
        )
        assert {a.ecosystem for a in from_osv(record)} == {"PyPI", "npm"}

    def test_a_record_without_an_id_is_skipped(self):
        record = json.loads(json.dumps(OSV_RECORD))
        del record["id"]
        assert from_osv(record) == []


class TestAdvisorySet:
    def set_with(self, *advisories: Advisory) -> AdvisorySet:
        return AdvisorySet(advisories=list(advisories))

    def test_matching_requires_the_ecosystem_to_agree(self):
        # requests on PyPI and requests on npm are different packages.
        advisories = self.set_with(
            Advisory("A", "requests", "npm", "1.0.0", "99.0.0"),
        )
        assert advisories.matches("requests", "npm", "2.0.0")
        assert advisories.matches("requests", "PyPI", "2.0.0") == []

    def test_matching_respects_the_version_range(self):
        advisories = self.set_with(Advisory("A", "p", "PyPI", "1.0.0", "1.3.0"))
        assert advisories.matches("p", "PyPI", "1.2.0")
        assert advisories.matches("p", "PyPI", "1.3.0") == []

    def test_pypi_name_normalisation_applies_to_queries(self):
        advisories = self.set_with(Advisory("A", "example-lib", "PyPI", "1.0.0", "2.0.0"))
        assert advisories.matches("Example_Lib", "PyPI", "1.5.0")

    def test_loads_our_own_format(self, tmp_path):
        original = self.set_with(Advisory("A", "p", "PyPI", "1.0.0", "2.0.0"))
        path = original.write(tmp_path / "advisories.json")
        restored = AdvisorySet.load(path)
        assert len(restored) == 1
        assert restored.matches("p", "PyPI", "1.5.0")

    def test_loads_a_bare_list(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text(
            json.dumps([{"id": "A", "package": "p", "ecosystem": "PyPI",
                         "introduced": "1.0.0", "fixed": "2.0.0"}]),
            encoding="utf-8",
        )
        assert len(AdvisorySet.load(path)) == 1

    def test_loads_osv_records(self, tmp_path):
        path = tmp_path / "osv.json"
        path.write_text(json.dumps(OSV_RECORD), encoding="utf-8")
        loaded = AdvisorySet.load(path)
        assert loaded.matches("example-lib", "PyPI", "1.2.0")

    def test_loads_a_directory_of_osv_records(self, tmp_path):
        directory = tmp_path / "osv"
        (directory / "nested").mkdir(parents=True)
        (directory / "a.json").write_text(json.dumps(OSV_RECORD), encoding="utf-8")
        second = json.loads(json.dumps(OSV_RECORD))
        second["id"] = "GHSA-fixture-0002"
        (directory / "nested" / "b.json").write_text(json.dumps(second), encoding="utf-8")

        loaded = AdvisorySet.load(directory)
        assert len(loaded) == 2

    def test_an_unreadable_file_in_a_directory_is_skipped(self, tmp_path):
        directory = tmp_path / "osv"
        directory.mkdir()
        (directory / "good.json").write_text(json.dumps(OSV_RECORD), encoding="utf-8")
        (directory / "bad.json").write_text("{not json", encoding="utf-8")
        assert len(AdvisorySet.load(directory)) == 1

    def test_ecosystems_are_reported(self):
        advisories = self.set_with(
            Advisory("A", "p", "PyPI"), Advisory("B", "q", "npm")
        )
        assert advisories.ecosystems() == {"PyPI", "npm"}
