"""Local, offline collectors.

Every lane here reads local files only. Lanes 2 (exposure) and 3 (web) are not
implemented: both need target interaction, which requires the operating posture
ceiling to be raised above LOCAL_FIXTURE, and that is an explicit operator
decision rather than a build step.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory.signal.lanes.agent_config import AgentConfigLane
from greytheory.signal.lanes.dependency_manifest import DependencyManifestLane

__all__ = ["AgentConfigLane", "DependencyManifestLane"]
