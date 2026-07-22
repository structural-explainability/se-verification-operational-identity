"""tests/test_oi.py - Pytest wrapper over the finite-core checks.

The nine regression instances (7 cases and 2 from monotonicity_pair),
the oracle/fast differential over the exhaustive-small sweep and a
randomized batch, witness validity, the Proposition 5.5
pass-to-fail construction, and monotonic persistence of
failure under history extension are tested here.
"""

import pytest

from se_verification_operational_identity import fast, oracle
from se_verification_operational_identity.check import witness_valid
from se_verification_operational_identity.generate import (
    exhaustive_small,
    random_instances,
)
from se_verification_operational_identity.model import Instance, Kind, Verdict
from se_verification_operational_identity.oracle import (
    declared_relation,
    treatment_relation,
)
from se_verification_operational_identity.paper_cases import cases, monotonicity_pair


@pytest.mark.parametrize(
    "inst,want_v,want_k,want_sub",
    cases(),
    ids=[c[0].label for c in cases()],
)
def test_regression_classifies_as_asserted(
    inst: Instance,
    want_v: Verdict,
    want_k: Kind,
    want_sub: bool,
) -> None:
    res = oracle.audit(inst)
    assert res.verdict is want_v
    assert res.kind is want_k
    assert res.substitution is want_sub


@pytest.mark.parametrize(
    "inst",
    [c[0] for c in cases()],
    ids=[c[0].label for c in cases()],
)
def test_regression_oracle_matches_fast(inst: Instance):
    assert oracle.audit(inst).key() == fast.audit(inst).key()


@pytest.mark.parametrize("inst", list(exhaustive_small()))
def test_exhaustive_small_differential(inst: Instance):
    o, f = oracle.audit(inst), fast.audit(inst)
    assert o.key() == f.key(), inst.label
    assert witness_valid(inst, o)
    assert witness_valid(inst, f)


def test_randomized_differential():
    for inst in random_instances(20000, seed=0):
        o, f = oracle.audit(inst), fast.audit(inst)
        assert o.key() == f.key()
        assert witness_valid(inst, o)
        assert witness_valid(inst, f)


def test_monotonicity_prop_5_5():
    before, after = monotonicity_pair()
    assert oracle.audit(before).verdict is Verdict.PASS
    assert oracle.audit(after).verdict is Verdict.FAIL
    # witness on the extended instance satisfies Definition 4.3
    res = oracle.audit(after)
    assert res.witness is not None
    r, s = res.witness
    tau = declared_relation(after, after.tau)
    treat = treatment_relation(after)
    assert (r, s) in tau and (r, s) not in treat


def test_witness_persists_under_extension():
    """A fail never reverts to pass when history is only extended."""
    import random

    rng = random.Random(99)  # noqa: S311
    for _ in range(3000):
        base = next(random_instances(1, seed=rng.randint(0, 10**9)))
        from se_verification_operational_identity.model import Instance

        extra = tuple(
            (
                rng.choice(("a", "b", "c")),
                rng.choice(base.records),
                rng.choice(base.records),
            )
            for _ in range(rng.randint(1, 3))
        )
        ext = Instance(
            records=base.records,
            history=base.history + extra,
            tau=base.tau,
            sib=base.sib,
            surface=base.surface,
        )
        if oracle.audit(base).verdict is Verdict.FAIL:
            assert oracle.audit(ext).verdict is Verdict.FAIL
