"""Operation-count evidence for the fast closure step.

These tests record how the implementation behaves on measured histories.
They are supporting evidence and do not certify the bound of Theorem
oi.thm.decidable, which concerns all inputs.
"""

import pytest

from se_verification_operational_identity.audit_scaling import (
    count_closure,
    history_patterns,
)

SIZES = (1_000, 8_000, 64_000)
BOUND = 4.0


@pytest.mark.parametrize("n", SIZES)
def test_parent_steps_stay_within_a_small_multiple_of_input_size(n: int) -> None:
    for name, history in history_patterns(n).items():
        counter = count_closure(n, history)
        ratio = counter.parent_steps / (n + len(history))
        assert ratio <= BOUND, f"{name} n={n}: {ratio:.2f} steps per input item"


def test_per_item_cost_does_not_grow_with_size() -> None:
    for name in history_patterns(SIZES[0]):
        ratios = []
        for n in SIZES:
            history = history_patterns(n)[name]
            counter = count_closure(n, history)
            ratios.append(counter.parent_steps / (n + len(history)))
        assert ratios[-1] <= 1.5 * ratios[0] + 0.5, f"{name}: {ratios}"
