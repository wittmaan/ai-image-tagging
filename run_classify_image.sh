#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
conda_root="${CONDA_ROOT:-}"
if [[ -z "$conda_root" && -f "$script_dir/.env" ]]; then
    # Load local configuration only when CONDA_ROOT was not provided explicitly.
    source "$script_dir/.env"
    conda_root="${CONDA_ROOT:-}"
fi
if [[ -z "$conda_root" ]]; then
    conda_root="$(conda info --base 2>/dev/null || true)"
fi
python_executable="${conda_root}/envs/py311/python.exe"

if [[ ! -f "$python_executable" ]]; then
    printf 'Conda Python not found: %s\n' "$python_executable" >&2
    printf 'Set CONDA_ROOT to your Miniconda or Anaconda installation path.\n' >&2
    exit 1
fi

exec "$python_executable" "$script_dir/classify_image.py" "$@"
