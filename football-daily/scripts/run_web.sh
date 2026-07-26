#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"
exec streamlit run app/streamlit_app.py --server.headless true "$@"