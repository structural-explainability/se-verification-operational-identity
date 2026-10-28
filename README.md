# se-verification-operational-identity

[![PyPI](https://img.shields.io/pypi/v/se-verification-operational-identity?logo=pypi&label=pypi)](https://pypi.org/project/se-verification-operational-identity/)
[![Docs Site](https://img.shields.io/badge/docs-site-blue?logo=github)](https://structural-explainability.github.io/se-verification-operational-identity/)
[![Repo](https://img.shields.io/badge/repo-GitHub-black?logo=github)](https://github.com/structural-explainability/se-verification-operational-identity)
[![Python 3.14](https://img.shields.io/badge/python-3.14%2B-blue?logo=python)](./pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache--2.0-yellow.svg)](./LICENSE)
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

The purpose of this project is to give executable evidence that
the finite audit of SE-210 is implemented as the paper defines it.
It tests the core once `R`, the declared relation, the surfaces, and the
identified uses are supplied.

It provides evidence, not proof.
Agreement between implementations shows that independent derivations match.
Operation counts show how the fast procedure scales on the histories measured.
Neither certifies the asymptotic bound of the paper's decidability theorem,
and neither replaces the Lean formalization.

## Checks

Three derivations of the audit read the same raw `Instance`.
They share only the data classes in `audit_model.py`,
which contain no licence, signature, relation, or verdict logic.
`tests/test_audit_independence.py` enforces that boundary.

- **`audit_oracle.py`** builds the declared, alternative, and operational
  relations as explicit pair sets.
  It reads licences by literal membership,
  computes signatures from raw uses,
  closes relations by naive fixpoint,
  and compares by literal subset tests.
- **`audit_fast.py`** builds block labels with union-find
  (path compression and union by size),
  groups signature tuples,
  and compares inside declared blocks, with no `R x R` materialized.
- **`audit_edges.py`** decides faithfulness of a generated relation
  from its licensed steps alone, without any closure (`oi.prop.edges`).

Instances take two declared forms: a partition supplied directly,
or a relation generated from a history in which only licensed steps
contribute edges.
A family label never licenses a step (`oi.rem.neutral`).
The audit is three-valued.
It is indeterminate when a warrant is withheld,
when a use does not factor through the mechanism value,
or when an outcome is missing for a record.

The checks run over four sources of instances:

- **18 paper cases**, each tagged with the paper label it exercises, including
  substitution with a divergence witness (`oi.ex.loc-obj-fork`),
  substitution with a pass (`oi.rem.merging-substitution`),
  a neutral step that licenses nothing (`oi.rem.neutral`),
  and the indeterminate cases;
- **exhaustive partition sweeps**: every triple of declared, alternative,
  and operational partitions on 3 and 4 records (`--deep` adds 5 records);
- **exhaustive licence sweeps**: every pair of licensed-edge sets over a history
  that also contains unlicensed steps (`--deep` adds 4 records);
- **randomized instances**, 5,000 by default, with supplied and generated
  relations, one to three surfaces, withheld warrants, and uses that
  violate surface control or lack outcomes.

Each instance is also checked against properties the paper states:

- the two checkers agree and every witness is valid;
- exactly one of the four positions holds, and it matches the kind;
- faithfulness of a generated relation equals the edge test (`oi.prop.edges`);
- store faithfulness is faithfulness of every surface, and the joint
  surface has the store relation (`oi.prop.compose`);
- substitution forces an aligned failure when the declared relation has a pair
  the alternative separates, and forces a pass when it does not;
- the record-identity surface passes exactly when no distinct records merge;
- an omitted use that the mechanism controls turns a pass into a failure,
  and one it does not control makes the audit indeterminate;
- extra licensed steps never turn a failure into a pass,
  and unlicensed steps change nothing.

The run reports how often each branch was exercised,
because a property that is never exercised proves nothing.

## Seeded Faults

`tests/test_audit_mutants.py` plants deliberate errors.

A fault in the fast checker alone must be caught by the differential.
Thirteen are seeded:
the superseded construction in which every step joins its endpoints,
no transitive closure,
reading only the first use,
a store that passes when any surface passes,
reversed faithfulness,
swapped sub- and super-sibling,
positions compared globally instead of inside declared classes,
substitution taken as alignment,
substitution lost on a pass,
substitution without the regimes differing,
a witness that is not a witness,
an ignored warrant,
and an untested surface control.

A fault planted in both checkers at once models a shared misreading of the
paper.
A differential cannot see it, so these tests require the paper cases and the
property checks to catch it.

## Lean Conformance Vectors

`--emit-lean PATH` writes the oracle's audits of small supplied partitions as
Lean theorems about `SE.OperationalIdentity`, each closed by `decide`.
Lean then checks the verdict, the divergence position, and whether the
operational partition equals the alternative, using its own definitions.
Copy the generated file to `SETest/OperationalIdentity/Vectors.lean` in
`se-verification-operational-identity` and build it there.

## Run

```bash
uv sync --extra dev --extra docs --upgrade

uvx se-verification-operational-identity

# or with args
uvx se-verification-operational-identity --random 20000 --seed 0

# larger exhaustive sweeps
uvx se-verification-operational-identity --deep

# write Lean conformance vectors
uvx se-verification-operational-identity --emit-lean Vectors.lean
```

A nonzero exit from `se-verification-operational-identity` means a real
disagreement:
either the optimized procedure or the paper wording needs correction.

## Stipulated Licences

The paper's examples stipulate which steps are licensed.
They are assumptions of the examples,
not a rule that a family label licenses a step.

lu="licensed under"

| family           | lu RULE-C | lu RULE-S |     | family | lu LOC | lu OBJ |
| ---------------- | --------- | --------- | --- | ------ | ------ | ------ |
| refine-structure | yes       | no        |     | BF     | yes    | no     |
| revise-wording   | yes       | yes       |     |        |        |        |
| amend-content    | no        | yes       |     |        |        |        |

## Example Command Output

```shell
uv run se-verification-operational-identity --random 20000 --seed 0
```

```text
======================================================================
SE-210 finite audit verification
======================================================================
paper cases             : 18/18 as asserted
sweep partitions n=3   : 150 instances, all checks
sweep partitions n=4   : 3600 instances, all checks
sweep generated n=3    : 360 instances, all checks
randomized              : 20000 instances (seed 0)
----------------------------------------------------------------------
branch coverage (a property never exercised proves nothing):
  edges:faithful                  : 14134
  edges:unfaithful                : 3015
  history:pass-lost               : 1765
  omitted-use:controlled          : 5676
  omitted-use:uncontrolled        : 12259
  position:sibling-aligned        : 2150
  position:sibling-incomparable   : 1694
  position:sub-sibling            : 550
  position:super-sibling          : 1543
  record-surface:identity         : 5025
  record-surface:merging          : 14993
  store:fail                      : 5335
  store:pass                      : 10378
  substitution:with-pass          : 3223
  substitution:with-witness       : 472
----------------------------------------------------------------------
operation counts (supporting evidence, not a proof of the bound):
  n=1000    h=1000    parent-steps=3063     unions=836
  n=8000    h=8000    parent-steps=24974    unions=6702
  n=64000   h=64000   parent-steps=199200   unions=53636
----------------------------------------------------------------------
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

## Annotations

[Annotations](.annotations/annotations.md)

## Changelog

[CHANGELOG.md](./CHANGELOG.md)

## Citation

[CITATION.cff](./CITATION.cff)

## Documentation

[Documentation](https://structural-explainability.github.io/se-verification-operational-identity/) -
descriptive orientation

## Software Metadata

[CodeMeta (`codemeta.json`)](./codemeta.json)

## License

[Apache 2.0](./LICENSE)

## Repository Manifest

[SE_MANIFEST.toml](./SE_MANIFEST.toml) -
repository semantic ownership/scope
