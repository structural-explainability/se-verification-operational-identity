# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

---

## [0.2.1] - 2026-10-28

### Changed

- README and documentation fixes, minor but helpful

---

## [0.2.0] - 2026-10-28

### Changed

- Rebuilt the audit around the revised SE-210: a step contributes an edge only
  when it is independently licensed.
  A family label, including a neutral one, licenses nothing.
- Declared and alternative relations may be supplied as partitions or
  generated from licensed history steps.
- The audit is three-valued. It is indeterminate when a warrant is withheld,
  surface control fails, or an outcome is missing.
- Substitution is reported independently of the verdict.
  It can hold with a pass and with a divergence witness, and both are tested.
- The oracle, the fast checker, and a new edge-characterization checker share
  only data classes, and a test enforces that boundary.
- The fast checker uses union by size as well as path compression.
- Operation counts are reported as supporting evidence and not as proof of the
  asymptotic bound.

### Added

- Exhaustive sweeps over every triple of partitions (3 and 4 records, 5 with
  `--deep`) and over every pair of licensed-edge sets (3 records, 4 with
  `--deep`).
- Property checks for the edge characterization, store composition and the
  joint surface, substitution, the record-identity surface, omitted uses,
  history extension, and exclusivity of the four positions.
- Branch coverage reporting.
- Thirteen seeded faults in the fast checker and two shared misreadings that
  only the paper cases and property checks can catch.
- `--emit-lean`, which generates conformance vectors for independent
  checking against the Lean formalization.

### Removed

- The superseded modules and tests that treated preserving and neutral
  classifications as identity edges.

---

## [0.1.0] - 2026-07-22

### Added

- Added the initial Python package.
- Added the command-line interface.
- Added a transparent quadratic oracle that evaluates the SE-210 definitions
  using explicit record-pair relations.
- Added an optimized union-find and partition-label implementation of the
  finite procedure described in Theorem 5.2.
- Added regression cases derived from the paper's examples, propositions,
  classifications, and history-extension construction.
- Added deterministic exhaustive-small and seeded randomized differential
  testing.
- Added mutation tests for refinement direction, sibling classification,
  declared-class restriction, and regime substitution.
- Added documentation, CI, release automation, and the repository manifest.

---

## Notes on Versioning and Releases

- We use **SemVer**:
  - **MAJOR** - breaking changes
  - **MINOR** - backward-compatible features
  - **PATCH** - fixes, documentation, tests, tooling

Versions are driven by git tags.
Tag `vX.Y.Z` to release.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### Task 1. Update release metadata (manual edits)

1.1. `CITATION.cff` - update `version` and `date-released`
1.2. `CHANGELOG.md` - add section, move unreleased entries, update links, update release command
1.3. `pyproject.toml` - update build system `fallback-version`

### Task 2. Set up and Validate

```pwsh
.\sit.ps1

# Update GitHub Actions and pin all action references to immutable SHAs.
uvx gha-tools autoupdate --pin=all --write .github/workflows

# Audit the resulting GitHub configuration for security findings.
uvx zizmor@latest .github/
# one informational is okay

# Validate.
uvx cffconvert --validate
uvx se-manifest-schema validate-manifest --strict

# Format Markdown.
npx markdownlint-cli2 --fix

uv run python -c "import shutil; from pathlib import Path; shutil.rmtree(Path('dist'), ignore_errors=True)"

uv build
uvx twine check --strict dist/*

uv run python -c "import pathlib, zipfile; wheels=list(pathlib.Path('dist').glob('*.whl')); assert wheels, 'No wheel found'; wheel=wheels[-1]; names=zipfile.ZipFile(wheel).namelist(); packaged=[n for n in names if n.startswith('se_verification_operational_identity/')]; print(packaged); assert packaged, 'Package files missing from wheel'"

uvx --from (Get-ChildItem dist/*.whl).FullName se-verification-operational-identity --random 200
```

### Task 3. Commit and Push

```shell
git add -A
git commit -m "Prepare X.Y.Z"
git push -u origin main
```

Verify that all required GitHub Actions complete successfully.

### Task 4. Tag and Push the Release

After the required GitHub Actions succeed:

```shell
git tag vX.Y.Z -m "X.Y.Z"
git push origin vX.Y.Z
```

The `release-pypi.yml` workflow automatically creates the GitHub Release
and uploads the validated distribution artifacts.

Do not create a second release manually.
Verify the automated release in Task 5.

### Task 5. Verify the Release and Zenodo archive

The release workflow creates a GitHub Release automatically.
To verify:

```shell
gh release view vX.Y.Z  # confirm Release exists with notes + artifacts
gh run list --workflow=release-pypi.yml   # confirm the workflow succeeded
```

Confirm Zenodo shows a new version-specific DOI for this release
and that it remains linked under the
repository's [concept DOI](https://zenodo.org/records/21499598).

## Only As Needed (delete a tag)

```shell
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

## Links

[Unreleased]: https://github.com/structural-explainability/se-verification-operational-identity/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/structural-explainability/se-verification-operational-identity/releases/tag/v0.2.1
[0.2.0]: https://github.com/structural-explainability/se-verification-operational-identity/releases/tag/v0.2.0
[0.1.0]: https://github.com/structural-explainability/se-verification-operational-identity/releases/tag/v0.1.0

<!-- markdownlint-enable MD024 -->
