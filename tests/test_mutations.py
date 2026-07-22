"""tests/test_mutations.py - Tests for the differential verification harness.

These tests deliberately introduce incorrect versions of the optimized
checker and confirm that comparison with the transparent oracle detects each
error.

If a mutant survives, the differential test suite is not strong enough
to detect that failure mode.
"""

from collections.abc import Callable

import pytest

from se_verification_operational_identity import fast, oracle
from se_verification_operational_identity.generate import (
    exhaustive_small,
    random_instances,
)
from se_verification_operational_identity.model import (
    Instance,
    Kind,
    Result,
    Verdict,
)

type AuditFunction = Callable[[Instance], Result]


def diff_count(audit_mut: AuditFunction) -> tuple[int, int]:
    """Return how many generated instances distinguish a mutant from the oracle.

    The comparison pool combines the deterministic exhaustive-small sweep with
    3,000 reproducible random instances.

    A mutant is considered detected when it returns a different result from
    the oracle or raises an exception for an otherwise valid instance.
    """
    caught = 0
    pool = list(exhaustive_small()) + list(random_instances(3000, seed=7))

    for inst in pool:
        expected = oracle.audit(inst)

        try:
            actual = audit_mut(inst)
        except Exception:
            caught += 1
            continue

        if expected != actual:
            caught += 1

    return caught, len(pool)


def mut_reverse_faithful(inst: Instance) -> Result:
    """Reverse the faithfulness refinement direction incorrectly."""
    from se_verification_operational_identity.fast import labels, sig_labels

    tau = labels(inst, inst.tau)
    sig = sig_labels(inst)

    # WRONG: tests whether the operational partition refines the declaration.
    faithful = True
    for r in inst.records:
        for s in inst.records:
            if sig[r] == sig[s] and tau[r] != tau[s]:
                faithful = False

    if faithful:
        return Result(Verdict.PASS, Kind.NONE, False, None)

    return Result(Verdict.FAIL, Kind.UNPOSITIONED, False, None)


_original_audit = fast.audit


def mut_swap_subsuper(inst: Instance) -> Result:
    """Swap the sub-sibling and super-sibling classifications incorrectly."""
    result = _original_audit(inst)
    kind = result.kind

    if kind is Kind.SUB:
        kind = Kind.SUPER
    elif kind is Kind.SUPER:
        kind = Kind.SUB

    return Result(
        result.verdict,
        kind,
        result.substitution,
        result.witness,
    )


def mut_no_restriction(inst: Instance) -> Result:
    """Compare relations globally instead of inside declared classes."""
    from se_verification_operational_identity.fast import (
        block_homogeneous,
        blocks,
        labels,
        restricted_refines,
        sig_labels,
    )

    tau = labels(inst, inst.tau)
    sig = sig_labels(inst)
    tau_blocks = blocks(tau, inst.records)

    faithful = all(block_homogeneous(block, sig) for block in tau_blocks)
    if faithful:
        return Result(Verdict.PASS, Kind.NONE, False, None)

    if inst.sib is None:
        return Result(Verdict.FAIL, Kind.UNPOSITIONED, False, None)

    sib = labels(inst, inst.sib)

    # WRONG: performs one global comparison instead of comparing separately
    # inside each declared identity class.
    all_records = [list(inst.records)]
    op_sub_sib = all(restricted_refines(block, sig, sib) for block in all_records)
    sib_sub_op = all(restricted_refines(block, sib, sig) for block in all_records)

    if not any(not block_homogeneous(block, sib) for block in tau_blocks):
        return Result(Verdict.FAIL, Kind.UNPOSITIONED, False, None)

    kind = (
        Kind.ALIGNED
        if op_sub_sib and sib_sub_op
        else Kind.SUB
        if op_sub_sib
        else Kind.SUPER
        if sib_sub_op
        else Kind.INCOMPARABLE
    )

    return Result(Verdict.FAIL, kind, False, None)


def mut_sub_as_align(inst: Instance) -> Result:
    """Treat sibling alignment as regime substitution incorrectly."""
    result = _original_audit(inst)

    # WRONG: Proposition 4.14 shows that alignment does not imply substitution.
    substitution = result.kind is Kind.ALIGNED

    return Result(
        result.verdict,
        result.kind,
        substitution,
        result.witness,
    )


@pytest.mark.parametrize(
    ("name", "mutant"),
    [
        ("reverse faithfulness direction", mut_reverse_faithful),
        ("swap sub/super", mut_swap_subsuper),
        ("drop restriction to declared classes", mut_no_restriction),
        ("substitution := alignment", mut_sub_as_align),
    ],
)
def test_mutant_is_detected(name: str, mutant: AuditFunction) -> None:
    """Confirm that the differential harness detects a named mutant."""
    caught, total = diff_count(mutant)

    assert caught > 0, (
        f"Mutant survived: {name}. "
        f"The harness detected 0 differences across {total} instances."
    )
