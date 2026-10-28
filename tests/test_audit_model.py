"""Malformed supplied data is rejected, and incomplete data is not malformed."""

import pytest

from se_verification_operational_identity.audit_model import (
    Generated,
    Instance,
    Step,
    Supplied,
    Surface,
    identity_surface,
)

RECORDS = ("r0", "r1")


def _surface() -> Surface:
    return identity_surface("d", {"r0": 0, "r1": 1})


def test_duplicate_records_are_rejected() -> None:
    with pytest.raises(ValueError, match="distinct"):
        Instance(("r0", "r0"), Supplied((frozenset({"r0"}),)), (_surface(),))


def test_a_surface_is_required() -> None:
    with pytest.raises(ValueError, match="surface"):
        Instance(RECORDS, Supplied((frozenset(RECORDS),)), ())


@pytest.mark.parametrize(
    "blocks",
    [
        (frozenset({"r0"}),),
        (frozenset({"r0", "r1"}), frozenset({"r1"})),
        (frozenset({"r0", "r1"}), frozenset()),
    ],
)
def test_supplied_blocks_must_partition_the_records(
    blocks: tuple[frozenset[str], ...],
) -> None:
    with pytest.raises(ValueError, match="blocks"):
        Instance(RECORDS, Supplied(blocks), (_surface(),))


def test_history_endpoints_must_be_records() -> None:
    declared = Generated((Step("f", "r0", "x"),), frozenset())
    with pytest.raises(ValueError, match="endpoint"):
        Instance(RECORDS, declared, (_surface(),))


def test_mechanism_value_must_be_total() -> None:
    partial = Surface("d", {"r0": 0}, ())
    with pytest.raises(ValueError, match="total"):
        Instance(RECORDS, Supplied((frozenset(RECORDS),)), (partial,))


def test_a_use_may_not_mention_unknown_records() -> None:
    odd = Surface("d", {"r0": 0, "r1": 1}, ({"zzz": 1},))
    with pytest.raises(ValueError, match="outside"):
        Instance(RECORDS, Supplied((frozenset(RECORDS),)), (odd,))


def test_a_missing_outcome_is_not_malformed() -> None:
    gap = Surface("d", {"r0": 0, "r1": 1}, ({"r0": "a"},))
    assert Instance(RECORDS, Supplied((frozenset(RECORDS),)), (gap,)).surfaces == (gap,)
