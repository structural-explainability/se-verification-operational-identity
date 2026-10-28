"""audit_generate.py - Generate audit instances for differential testing.

Generators produce supplied :class:`Instance` values.
They contain no faithfulness, closure, classification, or verdict logic, so
they cannot share a defect with either checker.

Random generation covers:

- declared and alternative relations supplied as partitions or generated from
  histories in which only some steps are licensed,
- missing siblings,
- one to three surfaces with one or two uses,
- uses that violate surface control or are missing outcomes, and
- warrants with one precondition withheld.

The sweeps enumerate small domains completely:

- :func:`partition_sweep` covers every triple of partitions,
- :func:`generated_sweep` covers every pair of licensed-edge sets together
  with unlicensed steps that must be ignored.
"""

from collections.abc import Iterator
import itertools
import random

from .audit_model import (
    Generated,
    Instance,
    Record,
    Step,
    Supplied,
    Surface,
    Warrant,
    identity_surface,
    surface_from_tables,
)

_FAMILIES = ("a", "b", "c")


def set_partitions(n: int) -> Iterator[tuple[int, ...]]:
    """Yield every partition of ``n`` items as a restricted growth string.

    A restricted growth string assigns each item a block index.
    The first item is in block 0, and each item's index is at most one more
    than the largest index before it.
    """

    def extend(prefix: tuple[int, ...], top: int) -> Iterator[tuple[int, ...]]:
        if len(prefix) == n:
            yield prefix
            return
        for index in range(top + 2):
            yield from extend((*prefix, index), max(top, index))

    yield from extend((), -1)


def _records(n: int) -> tuple[Record, ...]:
    return tuple(f"r{i}" for i in range(n))


def supplied_from_labels(
    records: tuple[Record, ...], labels: tuple[int, ...]
) -> Supplied:
    """Build a supplied partition from a restricted growth string."""
    groups: dict[int, set[Record]] = {}
    for r, label in zip(records, labels, strict=True):
        groups.setdefault(label, set()).add(r)
    return Supplied(tuple(frozenset(g) for _, g in sorted(groups.items())))


def partition_sweep(n: int) -> Iterator[Instance]:
    """Yield every (declared, alternative or none, operational) partition triple.

    Each operational partition is realized by a surface whose single use
    reports the mechanism value.
    """
    records = _records(n)
    labelings = list(set_partitions(n))
    for tau_labels in labelings:
        tau = supplied_from_labels(records, tau_labels)
        for op_labels in labelings:
            surface = identity_surface("d", dict(zip(records, op_labels, strict=True)))
            yield Instance(records, tau, (surface,), None, label="partition-sweep")
            for sib_labels in labelings:
                yield Instance(
                    records,
                    tau,
                    (surface,),
                    supplied_from_labels(records, sib_labels),
                    label="partition-sweep",
                )


def _pair_steps(records: tuple[Record, ...]) -> tuple[Step, ...]:
    return tuple(Step("f", x, y) for x, y in itertools.combinations(records, 2))


def generated_sweep(n: int) -> Iterator[Instance]:
    """Yield every pair of licensed-edge sets over one history of all pairs.

    The history contains one step for each unordered pair of records.
    A subset of those steps is licensed.
    Unlicensed steps are present and must contribute nothing.
    The alternative is absent or generated the same way.
    """
    records = _records(n)
    all_steps = _pair_steps(records)
    subsets = [
        frozenset(c)
        for k in range(len(all_steps) + 1)
        for c in itertools.combinations(all_steps, k)
    ]
    surfaces = [
        identity_surface("d", dict(zip(records, labels, strict=True)))
        for labels in set_partitions(n)
    ]
    for tau_licensed in subsets:
        tau = Generated(all_steps, tau_licensed)
        for surface in surfaces:
            yield Instance(records, tau, (surface,), None, label="generated-sweep")
            for sib_licensed in subsets:
                yield Instance(
                    records,
                    tau,
                    (surface,),
                    Generated(all_steps, sib_licensed),
                    label="generated-sweep",
                )


def _random_supplied(records: tuple[Record, ...], rng: random.Random) -> Supplied:
    bins = rng.randint(1, len(records))
    labels = tuple(rng.randint(0, bins - 1) for _ in records)
    groups: dict[int, set[Record]] = {}
    for r, label in zip(records, labels, strict=True):
        groups.setdefault(label, set()).add(r)
    return Supplied(tuple(frozenset(g) for g in groups.values()))


def _random_generated(records: tuple[Record, ...], rng: random.Random) -> Generated:
    count = rng.randint(0, 2 * len(records))
    history = tuple(
        Step(rng.choice(_FAMILIES), rng.choice(records), rng.choice(records))
        for _ in range(count)
    )
    chance = rng.random()
    licensed = frozenset(s for s in history if rng.random() < chance)
    return Generated(history, licensed)


def _random_relation(
    records: tuple[Record, ...], rng: random.Random
) -> Supplied | Generated:
    if rng.random() < 0.5:
        return _random_supplied(records, rng)
    return _random_generated(records, rng)


def _random_surface(
    name: str, records: tuple[Record, ...], rng: random.Random
) -> Surface:
    """Return a random surface, occasionally violating control or computability."""
    bins = rng.randint(1, len(records))
    value = {r: rng.randint(0, bins - 1) for r in records}
    seen = sorted(set(value.values()))
    tables = []
    for _ in range(rng.randint(1, 2)):
        outcomes = rng.randint(1, len(seen))
        tables.append({v: rng.randint(0, outcomes - 1) for v in seen})
    surface = surface_from_tables(name, value, tables)
    roll = rng.random()
    if roll < 0.04:
        broken = {r: rng.randint(0, 2) for r in records}
        return Surface(name, surface.value, (*surface.uses, broken))
    if roll < 0.08:
        dropped = rng.choice(records)
        first = {r: o for r, o in surface.uses[0].items() if r != dropped}
        return Surface(name, surface.value, (first, *surface.uses[1:]))
    return surface


def _random_warrant(rng: random.Random) -> Warrant:
    if rng.random() < 0.9:
        return Warrant()
    flags = [True, True, True, True]
    flags[rng.randrange(4)] = False
    return Warrant(flags[0], flags[1], flags[2], flags[3])


def random_instance(rng: random.Random) -> Instance:
    """Return one random well-formed instance."""
    n = rng.randint(2, 6)
    records = _records(n)
    declared = _random_relation(records, rng)
    sibling = _random_relation(records, rng) if rng.random() < 0.7 else None
    surfaces = tuple(
        _random_surface(f"d{i}", records, rng) for i in range(rng.randint(1, 3))
    )
    return Instance(
        records, declared, surfaces, sibling, _random_warrant(rng), "random"
    )


def random_instances(count: int, seed: int = 0) -> Iterator[Instance]:
    """Yield a reproducible sequence of random instances."""
    rng = random.Random(seed)
    for _ in range(count):
        yield random_instance(rng)
