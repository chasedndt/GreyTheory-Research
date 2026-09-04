"""GreyTheory's transparent, decision-support-only hypothesis engine."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory.hypothesis.domain import (
    ASSESSED_FACTORS,
    SYSTEM_DERIVED_FACTORS,
    AssessmentSource,
    FactorAssessment,
    FactorDirection,
    FactorExplanation,
    FactorWeight,
    HypothesisRankingError,
    HypothesisRankingInput,
    QueuePartition,
    RankedHypothesis,
    RankingFactor,
    RankingPolicy,
    ResearchQueue,
    conservative_local_policy,
    parse_ranking_inputs,
)
from greytheory.hypothesis.engine import HypothesisRanker
from greytheory.hypothesis.fixtures import (
    FIXTURE_TIME,
    LocalRankingFixture,
    build_local_ranking_fixture,
    populate_local_ranking_store,
    run_local_ranking_fixture,
)
from greytheory.hypothesis.io import write_ranking_payload, write_research_queue

__all__ = [
    "ASSESSED_FACTORS",
    "SYSTEM_DERIVED_FACTORS",
    "AssessmentSource",
    "FIXTURE_TIME",
    "FactorAssessment",
    "FactorDirection",
    "FactorExplanation",
    "FactorWeight",
    "HypothesisRanker",
    "HypothesisRankingError",
    "HypothesisRankingInput",
    "LocalRankingFixture",
    "QueuePartition",
    "RankedHypothesis",
    "RankingFactor",
    "RankingPolicy",
    "ResearchQueue",
    "build_local_ranking_fixture",
    "conservative_local_policy",
    "parse_ranking_inputs",
    "populate_local_ranking_store",
    "run_local_ranking_fixture",
    "write_ranking_payload",
    "write_research_queue",
]
