"""generate.py - Generate well-formed audit instances for differential testing.

This module produces supplied :class:`Instance` values without computing the
audit results they should receive.
It contains no faithfulness, refinement,
classification, substitution, or witness logic.

Random generation exercises varied regions of the finite input space,
including:

- empty and dense transformation histories,
- declared regimes with and without siblings,
- differing family classifications,
- implementation surfaces that merge or separate records, and
- multiple identified uses that may further merge mechanism values.

The deterministic exhaustive-small generator covers every selected
combination over three records.

Together, these generators provide inputs against which the
transparent oracle and optimized checker can be compared independently.
"""

from collections.abc import Iterator
import itertools
import random

from .model import Cls, Instance, Regime, Surface

_FAMILIES = ("a", "b", "c")
_CLS_CHOICES = (Cls.PRS, Cls.BRK, Cls.NEU)  # N/A excluded by well-formedness


def _random_regime(name: str, rng: random.Random, sibling: str | None) -> Regime:
    classify = {f: rng.choice(_CLS_CHOICES) for f in _FAMILIES}
    return Regime(name, classify, sibling=sibling)


def _random_surface(records: tuple[str, ...], rng: random.Random) -> Surface:
    """Return a random mechanism surface over the supplied records.

    Records are first assigned to a random number of mechanism-value groups.
    Records with the same assigned value therefore share the same mechanism
    observation.

    The surface then receives one or two identified uses.
    Each use maps the observed mechanism values
    to a random set of outcomes and may merge values
    that the mechanism itself distinguishes.

    Every generated use is a total function of the generated mechanism values,
    so surface control holds by construction.
    """
    nbins = rng.randint(1, len(records))
    value = {r: rng.randint(0, nbins - 1) for r in records}
    seen_values = sorted(set(value.values()))
    # One or two uses, each a random collapse of the value set to outcomes.
    n_uses = rng.randint(1, 2)
    uses = []
    for _ in range(n_uses):
        n_out = rng.randint(1, len(seen_values))
        table = {v: rng.randint(0, n_out - 1) for v in seen_values}
        uses.append(table)
    return Surface("d", value, uses)


def random_instance(rng: random.Random) -> Instance:
    """Return one randomly generated, well-formed audit instance.

    The instance contains between two and six records, a randomly sized
    transformation history, random classifications for each transformation
    family, and a random implementation surface.

    Most generated declared regimes receive a sibling so the four-way
    classification is exercised frequently.
    The remaining instances omit a sibling
    and exercise the unpositioned case.

    The function generates inputs only.
    It does not determine or encode the
    audit result expected from either checker.
    """
    n = rng.randint(2, 6)
    records = tuple(f"r{i}" for i in range(n))
    hist_len = rng.randint(0, 2 * n)
    history = tuple(
        (rng.choice(_FAMILIES), rng.choice(records), rng.choice(records))
        for _ in range(hist_len)
    )
    with_sibling = rng.random() < 0.7
    if with_sibling:
        tau = _random_regime("TAU", rng, sibling="SIB")
        sib = _random_regime("SIB", rng, sibling="TAU")
    else:
        tau = _random_regime("TAU", rng, sibling=None)
        sib = None
    surface = _random_surface(records, rng)
    return Instance(
        records=records,
        history=history,
        tau=tau,
        surface=surface,
        sib=sib,
        label="random",
    )


def random_instances(count: int, seed: int = 0) -> Iterator[Instance]:
    """Yield a reproducible sequence of random audit instances.

    ``count`` determines how many instances are produced.
    ``seed`` initializes a private pseudorandom generator,
    so repeated calls with the same arguments
    yield the same sequence.

    Reproducibility allows a reported disagreement between the two checkers to
    be regenerated exactly.
    """
    rng = random.Random(seed)  # noqa: S311
    for _ in range(count):
        yield random_instance(rng)


def exhaustive_small() -> Iterator[Instance]:
    """Yield a deterministic sweep of selected three-record instances.

    The sweep varies:

    - four representative histories,
    - every pair of preserving, breaking, and neutral classifications for the
      declared and sibling regimes, and
    - all five partitions of a three-record set as operational outcomes.

    Each surface uses an identity outcome map, so its treatment partition is
    exactly its mechanism-value partition.

    These are the smallest cases in which refinement direction, sibling
    comparison, and crossing partitions can be distinguished clearly.
    The sweep is intended to expose directional and classification errors that
    might be obscured in larger random instances.
    """
    records = ("r0", "r1", "r2")
    histories = [
        (),
        (("a", "r0", "r1"),),
        (("a", "r0", "r1"), ("a", "r1", "r2")),
        (("a", "r0", "r1"), ("a", "r0", "r2")),
    ]
    # All surfaces on 3 records: value maps up to relabeling are the set
    # partitions of {r0,r1,r2}; use a single identity use so the signature
    # partition equals the value partition.
    value_partitions = [
        {"r0": 0, "r1": 1, "r2": 2},
        {"r0": 0, "r1": 0, "r2": 1},
        {"r0": 0, "r1": 1, "r2": 0},
        {"r0": 1, "r1": 0, "r2": 0},
        {"r0": 0, "r1": 0, "r2": 0},
    ]
    cls_pairs = list(itertools.product(_CLS_CHOICES, repeat=2))
    for h in histories:
        for tau_cls, sib_cls in cls_pairs:
            tau = Regime("TAU", {"a": tau_cls}, sibling="SIB")
            sib = Regime("SIB", {"a": sib_cls}, sibling="TAU")
            for vp in value_partitions:
                table = {v: v for v in set(vp.values())}
                yield Instance(
                    records=records,
                    history=h,
                    tau=tau,
                    sib=sib,
                    surface=Surface("d", dict(vp), [table]),
                    label="exhaustive-small",
                )
