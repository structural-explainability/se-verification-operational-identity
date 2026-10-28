"""Oracle and fast checkers agree on swept and random instances."""

import random

from se_verification_operational_identity.audit_check import check_instance
from se_verification_operational_identity.audit_generate import (
    generated_sweep,
    partition_sweep,
    random_instances,
)
from se_verification_operational_identity.audit_model import Instance
from se_verification_operational_identity.audit_properties import (
    Coverage,
    check_agreement,
    check_edge_characterization,
    check_positions,
    check_substitution,
)


def _sweep_problems(instances: list[Instance]) -> list[str]:
    cov = Coverage()
    problems: list[str] = []
    for inst in instances:
        problems += check_agreement(inst)
        problems += check_positions(inst, cov)
        problems += check_substitution(inst, cov)
    return problems


def test_partition_sweep_three_records() -> None:
    assert _sweep_problems(list(partition_sweep(3))) == []


def test_partition_sweep_four_records() -> None:
    instances = list(partition_sweep(4))
    assert len(instances) == 15 * 15 * 16
    assert _sweep_problems(instances) == []


def test_generated_sweep_three_records() -> None:
    cov = Coverage()
    problems: list[str] = []
    for inst in generated_sweep(3):
        problems += check_agreement(inst)
        problems += check_edge_characterization(inst, cov)
    assert problems == []
    assert cov.counts["edges:faithful"] > 0
    assert cov.counts["edges:unfaithful"] > 0


def test_random_instances_every_property() -> None:
    cov = Coverage()
    rng = random.Random(1)
    problems: list[str] = []
    for inst in random_instances(3000, seed=0):
        problems += check_instance(inst, cov, rng)
    assert problems == []
    for branch in (
        "substitution:with-pass",
        "substitution:with-witness",
        "omitted-use:controlled",
        "omitted-use:uncontrolled",
        "history:pass-lost",
        "store:fail",
        "store:pass",
    ):
        assert cov.counts.get(branch, 0) > 0, branch
