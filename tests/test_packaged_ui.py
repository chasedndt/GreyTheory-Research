from __future__ import annotations

from pathlib import Path

import pytest

from greytheory_local.cli import build_parser, session_token_from_environment
from greytheory_local.packaged_ui import packaged_ui_root


def test_packaged_ui_root_requires_a_built_index(tmp_path: Path) -> None:
    assert packaged_ui_root(tmp_path) is None
    (tmp_path / "ui").mkdir()
    assert packaged_ui_root(tmp_path) is None
    (tmp_path / "ui" / "index.html").write_text("GreyTheory", encoding="utf-8")
    assert packaged_ui_root(tmp_path) == (tmp_path / "ui").resolve()


def test_cli_can_explicitly_disable_or_override_the_bundled_ui() -> None:
    parser = build_parser()
    assert parser.parse_args(["--no-ui"]).no_ui is True
    assert parser.parse_args(["--ui-root", "built-ui"]).ui_root == "built-ui"
    with pytest.raises(SystemExit):
        parser.parse_args(["--no-ui", "--ui-root", "built-ui"])


def test_session_token_environment_is_explicit_and_never_falls_back() -> None:
    assert session_token_from_environment(False, {"GREYTHEORY_SESSION_TOKEN": "ignored"}) is None
    assert session_token_from_environment(True, {"GREYTHEORY_SESSION_TOKEN": "ephemeral-token"}) == "ephemeral-token"
    with pytest.raises(ValueError, match="GREYTHEORY_SESSION_TOKEN is required"):
        session_token_from_environment(True, {})
