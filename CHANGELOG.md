# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

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
- Versions are driven by git tags. Tag `vX.Y.Z` to release.
- Docs are deployed per version tag and aliased to **latest**.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### Task 1. Update release metadata (manual edits)

1.1. `CITATION.cff` - update `version` and `date-released`
1.2. CHANGELOG.md: add section, move unreleased entries, update links
1.3. `pyproject.toml` - update build system `fallback-version`

### Task 2. Validate

```shell
uv sync --extra dev --extra docs --upgrade
uvx pre-commit install

git add -A
uvx pre-commit run --all-files
uvx pre-commit run --all-files

uv run pyright
uv run pytest
uv run se-verification-operational-identity --random 20000 --seed 0
uv run zensical build

uvx se-manifest-schema validate-manifest --strict

uv run python -c "import shutil; from pathlib import Path; shutil.rmtree(Path('dist'), ignore_errors=True)"

uv build
uvx twine check --strict dist/*

uv run python -c "import pathlib, zipfile; wheels=list(pathlib.Path('dist').glob('*.whl')); assert wheels, 'No wheel found'; wheel=wheels[-1]; names=zipfile.ZipFile(wheel).namelist(); packaged=[n for n in names if n.startswith('se_verification_operational_identity/')]; print(packaged); assert packaged, 'Package files missing from wheel'"
```

### Task 3. Commit, push, tag

```shell
git add -A
git commit -m "Prepare X.Y.Z"
git push -u origin main
```

Verify actions run on GitHub. After success:

```shell
git tag vX.Y.Z -m "X.Y.Z"
git push origin vX.Y.Z
```

## Only As Needed (delete a tag)

```shell
git tag -d vX.Z.Y
git push origin :refs/tags/vX.Z.Y
```

## Links

[Unreleased]: https://github.com/structural-explainability/se-verification-operational-identity/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/structural-explainability/se-verification-operational-identity/releases/tag/v0.1.0

<!-- markdownlint-enable MD024 -->
