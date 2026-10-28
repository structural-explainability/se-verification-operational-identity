"""audit_scaling.py - Operation counts for the fast checker's closure step.

These measurements are supporting evidence.
Counting pointer traversals on a few histories cannot establish the
asymptotic bound of Theorem ``oi.thm.decidable``.
That bound is a statement about all inputs, and a count is a statement about
the inputs measured.
The counts do show whether the implementation behaves as the bound predicts
on chains, stars, balanced merges, and random histories, and they would
expose a quadratic implementation immediately.
"""

import random

from .audit_fast import OpCounter, declared_labels
from .audit_model import Generated, Record, Step


def _records(n: int) -> tuple[Record, ...]:
    return tuple(f"r{i}" for i in range(n))


def history_patterns(n: int, seed: int = 0) -> dict[str, tuple[Step, ...]]:
    """Return named histories of about ``n`` steps over ``n`` records.

    The patterns are a chain, a star, balanced pairwise merging, and random
    pairs.
    """
    records = _records(n)
    chain = tuple(Step("f", records[i], records[i + 1]) for i in range(n - 1))
    star = tuple(Step("f", records[0], records[i]) for i in range(1, n))
    balanced: list[Step] = []
    width = 1
    while width < n:
        for start in range(0, n - width, 2 * width):
            balanced.append(Step("f", records[start], records[start + width]))
        width *= 2
    rng = random.Random(seed)
    shuffled = tuple(
        Step("f", rng.choice(records), rng.choice(records)) for _ in range(n)
    )
    return {
        "chain": chain,
        "star": star,
        "balanced": tuple(balanced),
        "random": shuffled,
    }


def count_closure(n: int, history: tuple[Step, ...]) -> OpCounter:
    """Count the operations of building declared labels from a fully licensed history."""
    counter = OpCounter()
    declared = Generated(history, frozenset(history))
    declared_labels(_records(n), declared, counter)
    return counter


def scaling_rows(
    sizes: tuple[int, ...] = (1_000, 8_000, 64_000),
) -> list[tuple[int, int, int, int]]:
    """Return ``(n, h, parent_steps, unions)`` for the worst pattern at each size."""
    rows: list[tuple[int, int, int, int]] = []
    for n in sizes:
        measured = [
            (n, len(h), c.parent_steps, c.unions)
            for h in history_patterns(n).values()
            for c in (count_closure(n, h),)
        ]
        rows.append(max(measured, key=lambda row: row[2]))
    return rows
