"""The model gateway: classified at assembly, cited or refused, always inferred."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from greytheory.audit import AuditLog
from greytheory.models import (
    ContextFragment,
    DataClass,
    EchoProvider,
    GatewayError,
    ModelGateway,
    ModelRole,
    PolicyError,
    ProviderPolicy,
    TrustLabel,
    builtin_cases,
    run_suite,
)
from greytheory.provenance import Tag

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)


def local_policy(max_class: DataClass = DataClass.RAW_RESTRICTED) -> ProviderPolicy:
    return ProviderPolicy(
        "local.echo", local=True, max_data_class=max_class, approved_by="chase"
    )


def gateway(reply: str = "Answer [[ctx-1]].", **kw) -> ModelGateway:
    return ModelGateway(
        EchoProvider(reply),
        kw.pop("policy", local_policy()),
        clock=lambda: NOW,
        **kw,
    )


def fragment(**kw) -> ContextFragment:
    base = dict(
        id="ctx-1",
        text="A published scope table.",
        data_class=DataClass.PUBLIC,
        trust=TrustLabel.PUBLISHED,
    )
    base.update(kw)
    return ContextFragment(**base)


def assembled(gw: ModelGateway, **kw):
    base = dict(
        request_id="req-1",
        role=ModelRole.POLICY_ANALYST,
        instruction="Extract the proposed rules.",
        fragments=[fragment()],
    )
    base.update(kw)
    return gw.assemble(**base)


class TestProviderPolicy:
    def test_a_remote_provider_cannot_be_approved_for_raw_captures(self):
        with pytest.raises(PolicyError, match="do not leave the machine"):
            ProviderPolicy(
                "remote.x",
                local=False,
                max_data_class=DataClass.RAW_RESTRICTED,
                approved_by="chase",
            )

    def test_sensitive_approval_must_name_who_approved_it(self):
        with pytest.raises(PolicyError, match="must name who approved"):
            ProviderPolicy("remote.x", local=False, max_data_class=DataClass.TARGET_SENSITIVE)

    def test_a_remote_provider_may_hold_lower_classes(self):
        assert ProviderPolicy("remote.x", local=False, max_data_class=DataClass.PUBLIC)

    def test_an_unknown_class_name_is_the_most_restrictive(self):
        # I3: unknown resolves to denial, not to "probably fine".
        assert DataClass.parse("something-else") is DataClass.RAW_RESTRICTED

    def test_the_policy_must_match_the_provider(self):
        with pytest.raises(PolicyError, match="policy is for"):
            ModelGateway(EchoProvider(), ProviderPolicy("other", local=True, max_data_class=DataClass.PUBLIC))


class TestClassificationAtAssembly:
    def test_a_fragment_above_the_provider_ceiling_refuses(self):
        gw = gateway(policy=local_policy(DataClass.PUBLIC))
        with pytest.raises(PolicyError, match="approved only to PUBLIC"):
            assembled(gw, fragments=[fragment(data_class=DataClass.TARGET_SENSITIVE)])

    def test_a_fragment_above_the_role_ceiling_refuses(self):
        # The tutor role sees public material only, whatever the provider allows.
        gw = gateway()
        with pytest.raises(PolicyError, match="role 'tutor'"):
            assembled(
                gw,
                role=ModelRole.TUTOR,
                fragments=[fragment(data_class=DataClass.TARGET_SENSITIVE)],
            )

    def test_raw_restricted_says_why_plainly(self):
        gw = gateway(policy=local_policy(DataClass.TARGET_SENSITIVE))
        with pytest.raises(PolicyError, match="do not leave the machine"):
            assembled(gw, fragments=[fragment(data_class=DataClass.RAW_RESTRICTED)])

    def test_duplicate_context_ids_refuse(self):
        # A citation must resolve to exactly one fragment.
        gw = gateway()
        with pytest.raises(GatewayError, match="appears twice"):
            assembled(gw, fragments=[fragment(), fragment()])

    def test_the_instruction_may_not_contain_citations(self):
        gw = gateway()
        with pytest.raises(GatewayError, match="must not contain citations"):
            assembled(gw, instruction="Summarise [[ctx-1]].")

    def test_nothing_is_sent_during_assembly(self):
        gw = gateway()
        assembled(gw)
        assert gw.calls == 0


class TestUntrustedContent:
    def test_untrusted_fragments_are_fenced_and_labelled(self):
        gw = gateway()
        request = assembled(
            gw, fragments=[fragment(trust=TrustLabel.UNTRUSTED, origin="target")]
        )
        prompt = request.prompt()
        assert "<untrusted" in prompt
        assert "must not be followed" in prompt

    def test_their_presence_is_recorded_on_the_request(self):
        gw = gateway()
        assert assembled(gw, fragments=[fragment(trust=TrustLabel.UNTRUSTED)]).untrusted_present
        assert not assembled(gw).untrusted_present

    def test_their_presence_survives_onto_the_output(self, tmp_path):
        gw = gateway()
        output = gw.call(assembled(gw, fragments=[fragment(trust=TrustLabel.UNTRUSTED)]))
        assert output.untrusted_present


class TestCitations:
    def test_a_citation_that_does_not_resolve_is_refused(self):
        # An invented source, not a formatting error.
        gw = gateway(reply="It is confirmed [[ctx-99]].")
        with pytest.raises(GatewayError, match="cites context that was never supplied"):
            gw.call(assembled(gw))

    def test_a_role_requiring_citations_refuses_an_uncited_answer(self):
        gw = gateway(reply="The application is vulnerable.")
        with pytest.raises(GatewayError, match="must cite the context"):
            gw.call(assembled(gw))

    def test_the_tutor_role_is_exempt(self):
        gw = gateway(reply="Access control means the server decides.")
        output = gw.call(assembled(gw, role=ModelRole.TUTOR))
        assert output.citations == frozenset()

    def test_resolving_citations_are_recorded(self):
        gw = gateway(reply="Rule one applies [[ctx-1]].")
        assert gw.call(assembled(gw)).citations == {"ctx-1"}


class TestProvenance:
    def test_every_output_is_inferred(self):
        gw = gateway()
        output = gw.call(assembled(gw))
        assert output.is_inferred_only
        assert output.claims[0].tag is Tag.INFERRED

    def test_there_is_no_path_to_a_checked_claim(self):
        # Promotion needs a validator receipt, and a model cannot issue one.
        gw = gateway()
        output = gw.call(assembled(gw))
        assert all(c.check_ref is None for c in output.claims)

    def test_the_claim_names_the_provider_and_role(self):
        gw = gateway()
        output = gw.call(assembled(gw))
        assert "local.echo" in output.claims[0].source
        assert "policy_analyst" in output.claims[0].source


class TestBudget:
    class _Costly(EchoProvider):
        def complete(self, request):
            response = super().complete(request)
            return type(response)(
                text=response.text,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                model=response.model,
                cost=Decimal("1.00"),
            )

    def test_spending_accumulates(self):
        gw = ModelGateway(
            self._Costly("Answer [[ctx-1]]."), local_policy(), clock=lambda: NOW
        )
        gw.call(assembled(gw))
        assert gw.spent == Decimal("1.00")

    def test_an_exhausted_budget_refuses_rather_than_warns(self):
        gw = ModelGateway(
            self._Costly("Answer [[ctx-1]]."),
            local_policy(),
            budget=Decimal("1.00"),
            clock=lambda: NOW,
        )
        gw.call(assembled(gw))
        with pytest.raises(GatewayError, match="budget of 1.00 is exhausted"):
            gw.call(assembled(gw))


class TestAuditing:
    def test_calls_are_recorded_with_a_prompt_digest_not_the_prompt(self, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        gw = ModelGateway(
            EchoProvider("Answer [[ctx-1]]."), local_policy(), audit=audit, clock=lambda: NOW
        )
        gw.call(assembled(gw, fragments=[fragment(text="sensitive detail")]))
        record = audit.records()[-1]
        assert record.action == "model.call"
        assert len(record.detail["prompt_digest"]) == 64
        assert "sensitive detail" not in str(record.to_json())
        audit.verify()

    def test_refusals_are_recorded_too(self, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        gw = ModelGateway(
            EchoProvider("[[ctx-99]]"), local_policy(), audit=audit, clock=lambda: NOW
        )
        with pytest.raises(GatewayError):
            gw.call(assembled(gw))
        record = audit.records()[-1]
        assert record.action == "model.refused"
        assert "fabricated citations" in record.detail["refused"]

    def test_the_record_says_whether_the_provider_was_local(self, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        gw = ModelGateway(
            EchoProvider("Answer [[ctx-1]]."), local_policy(), audit=audit, clock=lambda: NOW
        )
        gw.call(assembled(gw))
        assert audit.records()[-1].detail["provider_local"] is True


class TestEvaluationHarness:
    def test_the_builtin_suite_is_clean_against_the_stub(self):
        report = run_suite(lambda: ModelGateway(EchoProvider(), local_policy()))
        assert report.clean, report.render()

    def test_it_covers_the_failure_modes_worth_catching(self):
        ids = {case.id for case in builtin_cases()}
        assert {
            "fabricated-citation",
            "no-citation",
            "raw-restricted-leak",
            "role-ceiling",
            "impact-overstatement",
            "states-uncertainty",
            "indirect-prompt-injection",
            "indirect-prompt-injection-compliance",
        } <= ids

    def test_negative_fixtures_assert_the_detector_fires(self):
        # Without this the suite cannot distinguish a working harness from a
        # bad model, and a permanently red suite is one nobody reads.
        negatives = [c for c in builtin_cases() if c.expect_problem]
        assert len(negatives) == 2

    def test_a_model_that_ignores_the_injection_passes_and_one_that_obeys_fails(self):
        cases = {c.id: c for c in builtin_cases()}
        report = run_suite(
            lambda: ModelGateway(EchoProvider(), local_policy()),
            [cases["indirect-prompt-injection"], cases["indirect-prompt-injection-compliance"]],
        )
        assert report.clean

    def test_a_silent_detector_is_reported_as_a_failure(self):
        cases = {c.id: c for c in builtin_cases()}
        broken = cases["impact-overstatement"]
        # Same case, but the model behaves — the negative fixture must notice.
        import dataclasses

        polite = dataclasses.replace(
            broken, reply="This may indicate an issue [[obs-1]]."
        )
        report = run_suite(lambda: ModelGateway(EchoProvider(), local_policy()), [polite])
        assert not report.clean
        assert "did not fire" in report.failed[0].detail
