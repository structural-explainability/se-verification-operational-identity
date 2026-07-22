# se-verification-operational-identity

[![PyPI](https://img.shields.io/pypi/v/se-verification-operational-identity?logo=pypi&label=pypi)](https://pypi.org/project/se-verification-operational-identity/)
[![Docs Site](https://img.shields.io/badge/docs-site-blue?logo=github)](https://structural-explainability.github.io/se-verification-operational-identity/)
[![Repo](https://img.shields.io/badge/repo-GitHub-black?logo=github)](https://github.com/structural-explainability/se-verification-operational-identity)
[![Python 3.14](https://img.shields.io/badge/python-3.14%2B-blue?logo=python)](./pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21499598.svg)](https://doi.org/10.5281/zenodo.21499598)

[![CI](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/ci-python-zensical.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/ci-python-zensical.yml)
[![Docs-Deploy](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/deploy-zensical.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/deploy-zensical.yml)
[![Pre-Release](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/pre-release.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/pre-release.yml)
[![Release](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/release-pypi.yml/badge.svg)](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/release-pypi.yml)
[![Links](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/links.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-verification-operational-identity/actions/workflows/links.yml)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-brightgreen.svg)](https://github.com/structural-explainability/se-verification-operational-identity/security)

> Executable verification of the **finite mathematical core** of
> SE-210, _Operational Identity: A Finite Audit of Declared and Implemented Rules
> of Sameness_.

## Purpose

The purpose of this project is to confirm that the algorithmic
and complexity claims are internally correct.
It tests the core once `R`, the partitions, surfaces, and uses are supplied.

## Checks

Two independent checkers consume the same supplied `Instance`:

- **`oracle.py`**: builds `~_tau`, `~_sib`, and `~=_d` as explicit pair sets,
  computes closures by naive fixpoint, and applies Definitions 4.1, 4.3, 4.7,
  4.8, and 4.10 by literal subset tests.
  No algorithmic shortcuts.
- **`fast.py`**: the near-linear procedure of Theorem 5.2: union-find
  closures, signature grouping for `pi_d`, and per-declared-block label
  comparison for faithfulness, witness detection, and the four-way
  classification, with no `R x R` ever materialized.

The two are diffed across four verdict fields:
faithfulness,
divergence-witness existence,
sibling-relative classification, and
regime substitution.

The diff runs across three sources of instances:

- the **seven regression cases** taken verbatim from the paper.
  These are
  faithful/pass;
  unpositioned;
  sibling-aligned with substitution (Ex. 4.11);
  aligned without substitution (Prop. 4.14);
  sub-sibling (Prop. 4.15 and the Section 6 `ruleTextVersion` worked example
  which uses the same construction;
  super-sibling (Rem. 4.16c);
  and sibling-incomparable (Rem. 4.16d);
- an **exhaustive-small** deterministic sweep of 180 instances over 3 records,
  covering every classification pair, every surface value-partition, and four histories;
- a **randomized** batch, 20,000 instances by default.

Alongside the diff, the harness checks three properties directly:
every extracted witness satisfies Definition 4.3;
the Proposition 5.5 before/after pair flips the verdict from pass to fail
when the history is extended;
and a fail never reverts to pass under history extension (anti-monotonicity).

## Check Failures

`mutation_test.py`-style injection confirms the differential catches each named
failure mode:

- reversed refinement direction,
- swapped sub/super,
- dropping the restriction to declared classes, and
- conflating substitution with alignment (the error Prop. 4.14 forbids).

These mutants all get flagged.

## Run

```bash
uv sync --extra dev --extra docs --upgrade

uvx se-verification-operational-identity

# or with args
uvx se-verification-operational-identity --random 20000 --seed 0
```

A nonzero exit from `se-verification-operational-identity` means a real
disagreement:
either the optimized procedure or the paper wording needs correction.

## Family Classifications

| family           | RULE-C | RULE-S |     | family | LOC | OBJ |
| ---------------- | ------ | ------ | --- | ------ | --- | --- |
| refine-structure | PRS    | BRK    |     | BF     | PRS | BRK |
| revise-wording   | PRS    | PRS    |     |        |     |     |
| amend-content    | BRK    | PRS    |     |        |     |     |

## Example Command Output

```shell
uv run se-verification-operational-identity --random 20000 --seed 0
```

```text
====================================================================
SE-210 finite-core verification
====================================================================
regression cases        : 7/7 classified as asserted
monotonicity (Prop 5.5) : ok
exhaustive-small diffs  : 180 instances, oracle vs fast
randomized diffs        : 20000 instances (seed 0)
monotone property       : ok
--------------------------------------------------------------------
RESULT: all checks passed
```

## Developer Command Reference

<details>
<summary>Show command reference</summary>

### In a machine terminal

Open a machine terminal where you want the project:

```shell
git clone https://github.com/structural-explainability/se-verification-operational-identity

cd se-verification-operational-identity
code .
```

### In a VS Code terminal

```shell
uv self update
uv python pin 3.14
uv lock --upgrade
uv sync --extra dev --extra docs --upgrade

uvx pre-commit install
uvx pre-commit autoupdate

git add -A
uvx pre-commit run --all-files
# repeat if changes were made
uvx pre-commit run --all-files

# run locally with defaults
uv run se-verification-operational-identity

# or run locally with args
uv run se-verification-operational-identity --random 20000 --seed 0

# A nonzero exit from `se-verification-operational-identity` means a real
# disagreement: either the optimized procedure or the paper wording needs
# correction.

# types, tests, docs
uv run pyright
uv run pytest
uv run zensical build

# save progress
git add -A
git commit -m "update"
git push -u origin main
```

Merging GH Agent code example

```shell
git fetch origin copilot/analyze-test-coverage
git switch copilot/analyze-test-coverage
uv sync --extra dev --extra docs --upgrade
uvx pre-commit run --all-files
git status

git add -A
uvx pre-commit run --all-files

uv run pyright
uv run pytest

uv run se-verification-operational-identity --random 20000 --seed 0

uv run zensical build

git add -A
git commit -m "fix copilot generated test formatting"
git push
```

</details>

## Paper Links

- [Operational Identity Paper: GitHub Repository](https://github.com/structural-explainability/paper-210-operational-identity)

## Citation

[CITATION.cff](./CITATION.cff)

## Software Metadata

[CodeMeta (`codemeta.json`)](./codemeta.json)

## License

[MIT](./LICENSE)

## Repository Manifest

[SE_MANIFEST.toml](./SE_MANIFEST.toml)
