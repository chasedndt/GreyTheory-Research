"""Discovery for the optional workbench UI bundled in an installed wheel."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from pathlib import Path


def packaged_ui_root(package_dir: str | Path | None = None) -> Path | None:
    """Return a validated bundled UI directory, or ``None`` in a source checkout."""

    root = Path(package_dir).resolve() if package_dir is not None else Path(__file__).resolve().parent
    ui_root = root / "ui"
    if ui_root.is_dir() and (ui_root / "index.html").is_file():
        return ui_root
    return None


__all__ = ["packaged_ui_root"]
