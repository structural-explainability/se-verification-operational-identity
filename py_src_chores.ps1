#Requires -Version 7.0

<#
============================================================
py_src_chores.ps1 (ALL-PY-SRC-REPOS)
============================================================
Updated: 2026-06-27

Update dependencies, lint, test, and build docs.
For Python source repos only.

Run with:
.\py_src_chores.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

# run common chores
uv run ruff format .
uv run ruff check . --fix

uv run pyright
uv run pytest
uv run zensical build

uv run python -c "import shutil; from pathlib import Path; shutil.rmtree(Path('dist'), ignore_errors=True)"

uv build
uvx twine check --strict dist/*

uv run python -c "import pathlib, zipfile; wheels=list(pathlib.Path('dist').glob('*.whl')); assert wheels, 'No wheel found'; wheel=wheels[-1]; names=zipfile.ZipFile(wheel).namelist(); packaged=[n for n in names if n.startswith('se_verification_operational_identity/')]; print(packaged); assert packaged, 'Package files missing from wheel'"

Write-Host "All commands executed successfully."
Write-Host "Run a Python module to verify .venv/ is working correctly."
