"""Paper-case regressions for both checkers and every per-instance property."""

import random

import pytest

from se_verification_operational_identity import audit_fast, audit_oracle
from se_verification_operational_identity.audit_cases import (
    Case,
    cases,
    nonmonotone_pair,
    omitted_surface_example,
)
from se_verification_operational_identity.audit_check import check_instance
from se_verification_operational_identity.audit_model import Verdict
from se_verification_operational_identity.audit_properties import Coverage

ALL_CASES = cases()
IDS = [f"{c.inst.label} [{c.paper}]" for c in ALL_CASES]


@pytest.mark.parametrize("case", ALL_CASES, ids=IDS)
def test_oracle_matches_paper(case: Case) -> None:
    assert audit_oracle.audit(case.inst).key() == case.expected()


@pytest.mark.parametrize("case", ALL_CASES, ids=IDS)
def test_fast_matches_paper(case: Case) -> None:
    assert audit_fast.audit(case.inst).key() == case.expected()


@pytest.mark.parametrize("case", ALL_CASES, ids=IDS)
def test_every_property_holds_on_paper_cases(case: Case) -> None:
    assert check_instance(case.inst, Coverage(), random.Random(0)) == []


def test_substitution_with_pass_and_with_witness_are_both_present() -> None:
    """Substitution does not by itself give a witness; both outcomes occur."""
    by_label = {c.inst.label: c for c in ALL_CASES}
    with_pass = by_label["substitution with a PASS"]
    with_witness = by_label["fork: substitution with a witness"]
    assert with_pass.substitution and with_pass.verdict is Verdict.PASS
    assert with_witness.substitution and with_witness.verdict is Verdict.FAIL


def test_nonmonotone_pair() -> None:
    before, after = nonmonotone_pair()
    assert audit_oracle.audit(before).verdict is Verdict.PASS
    assert audit_oracle.audit(after).verdict is Verdict.FAIL
    assert audit_fast.audit(before).verdict is Verdict.PASS
    assert audit_fast.audit(after).verdict is Verdict.FAIL


def test_omitted_joint_surface_overturns_a_store_pass() -> None:
    inst, joint = omitted_surface_example()
    assert audit_oracle.audit_store(inst).verdict is Verdict.PASS
    assert audit_oracle.audit_surface(inst, joint).verdict is Verdict.FAIL
    from dataclasses import replace

    wider = replace(inst, surfaces=(*inst.surfaces, joint))
    assert audit_oracle.audit_store(wider).verdict is Verdict.FAIL
    assert audit_fast.audit_store(wider).verdict is Verdict.FAIL
