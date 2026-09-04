"""Private, atomic writeback for target-specific research queues."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import os
from pathlib import Path

from greytheory.evidence import find_repository_root
from typing import Any, Mapping

from greytheory.hypothesis.domain import HypothesisRankingError, ResearchQueue


def write_research_queue(
    path: str | os.PathLike[str], queue: ResearchQueue
) -> Path:
    """Write a queue outside Git so target-specific prioritisation stays private."""

    return write_ranking_payload(path, queue.to_dict())


def write_ranking_payload(
    path: str | os.PathLike[str], payload: Mapping[str, Any]
) -> Path:
    """Atomically write a ranking queue or synthetic verification receipt."""

    output = Path(path).expanduser().resolve()
    if find_repository_root(output) is not None:
        raise HypothesisRankingError(
            "research queues cannot be written inside a git working tree; "
            "use a private local data root"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    return output
