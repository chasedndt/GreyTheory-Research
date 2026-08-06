"""Command line surface for the Authority Plane.

Deliberately small. It exposes the four things an operator needs to do without
writing Python: compile a programme, review a clean contract, ask the gate a
question, and verify the audit chain.

    greytheory compile fixtures/programmes/mock-verified.json -o build/contract.json
    greytheory review build/contract.json --reviewer chase
    greytheory check build/contract.json --asset app.mock-verified.test --level LOCAL_FIXTURE
    greytheory audit-verify audit.jsonl
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from greytheory.audit import AuditLog, AuditVerificationError
from greytheory.authority.compiler import compile_contract, mark_reviewed
from greytheory.authority.gate import AccessRequest, AuthorityLevel, Gate
from greytheory.authority.scope import ScopeContract

DEFAULT_AUDIT = "audit.jsonl"


def _load(path: str) -> tuple[dict, str]:
    raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw), raw


def cmd_compile(args: argparse.Namespace) -> int:
    programme, raw = _load(args.programme)
    result = compile_contract(programme, raw_source=raw)
    contract = result.contract

    audit = AuditLog(args.audit)
    audit.append(
        actor=args.actor,
        action="contract.compile",
        detail={
            "programme": args.programme,
            "status": contract.status.value,
            "ambiguities": contract.ambiguities,
            "fingerprint": contract.fingerprint(),
        },
    )

    print(f"contract:    {contract.id}")
    print(f"programme:   {contract.programme_id}")
    print(f"status:      {contract.status.value.upper()}")
    print(f"fingerprint: {contract.fingerprint()[:16]}...")
    print(f"granted:     {contract.max_authority}")
    if contract.ambiguities:
        print(f"\nBLOCKED by {len(contract.ambiguities)} ambiguity/ies:")
        for item in contract.ambiguities:
            print(f"  - {item}")
        print("\nResolve these in the programme source and recompile.")
    else:
        print("\nCompiled clean. Status is PENDING_REVIEW - it grants nothing until")
        print("a human reviews it:  greytheory review <contract> --reviewer <name>")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(contract.to_dict(), indent=2), encoding="utf-8"
        )
        print(f"\nwritten: {args.out}")

    return 1 if result.blocked else 0


def cmd_review(args: argparse.Namespace) -> int:
    data, _ = _load(args.contract)
    contract = ScopeContract.from_dict(data)
    try:
        mark_reviewed(contract, reviewer=args.reviewer)
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    AuditLog(args.audit).append(
        actor=args.reviewer,
        action="contract.review",
        authority_ref=contract.fingerprint(),
        detail={"contract_id": contract.id, "status": contract.status.value},
    )
    Path(args.contract).write_text(
        json.dumps(contract.to_dict(), indent=2), encoding="utf-8"
    )
    print(f"{contract.id} reviewed by {args.reviewer} -> VERIFIED")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    data, _ = _load(args.contract)
    contract = ScopeContract.from_dict(data)
    gate = Gate(
        AuditLog(args.audit),
        posture_ceiling=AuthorityLevel.parse(args.posture),
    )
    decision = gate.evaluate(
        contract,
        AccessRequest(
            asset=args.asset,
            authority_level=AuthorityLevel.parse(args.level),
            actor=args.actor,
            technique=args.technique,
            derived_from=args.derived_from,
            purpose=args.purpose,
        ),
    )
    verdict = "ALLOW" if decision.allowed else "DENY"
    print(f"{verdict}  {args.asset}  [{decision.reason.value}]")
    print(f"  {decision.detail}")
    print(f"  authority_ref: {(decision.authority_ref or '-')[:16]}...")
    print(f"  audit seq:     {decision.audit_seq}")
    return 0 if decision.allowed else 2


def cmd_audit_verify(args: argparse.Namespace) -> int:
    log = AuditLog(args.audit)
    count = len(log.records())
    try:
        log.verify()
    except AuditVerificationError as exc:
        print(f"AUDIT CHAIN BROKEN: {exc}", file=sys.stderr)
        return 1
    print(f"audit chain intact - {count} record(s) verified")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greytheory",
        description="GreyTheory AI - Authority Plane. No authorisation, no execution.",
    )
    parser.add_argument("--audit", default=DEFAULT_AUDIT, help="audit log path")
    parser.add_argument("--actor", default="operator", help="who is acting")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("compile", help="compile a programme record into a contract")
    p.add_argument("programme")
    p.add_argument("-o", "--out", help="write the compiled contract here")
    p.set_defaults(func=cmd_compile)

    p = sub.add_parser("review", help="human-review a clean contract into VERIFIED")
    p.add_argument("contract")
    p.add_argument("--reviewer", required=True)
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("check", help="ask the gate whether an action is permitted")
    p.add_argument("contract")
    p.add_argument("--asset", required=True)
    p.add_argument("--level", default="LOCAL_FIXTURE")
    p.add_argument("--technique")
    p.add_argument("--derived-from")
    p.add_argument("--purpose", default="")
    p.add_argument(
        "--posture",
        default="LOCAL_FIXTURE",
        help="system-wide authority ceiling (current posture is LOCAL_FIXTURE)",
    )
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("audit-verify", help="verify the audit hash chain")
    p.set_defaults(func=cmd_audit_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
