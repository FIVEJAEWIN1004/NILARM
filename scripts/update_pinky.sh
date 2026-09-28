#!/usr/bin/env bash
# Pull the latest NILARM from GitHub and rebuild the Pinky packages.
#   cd ~/NILARM && ./scripts/update_pinky.sh
# Refuses to run with local changes; fast-forward only (never reset/clean).
set -eo pipefail
repo="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd "${repo}"

if [[ -n "$(git status --porcelain)" ]]; then
    git status --short
    echo "update_pinky: local changes above; not updating. Commit, stash or" >&2
    echo "remove them yourself, then rerun." >&2
    exit 1
fi
before="$(git rev-parse --short HEAD)"
git pull --ff-only
echo "updated ${before} -> $(git rev-parse --short HEAD)"
exec "${repo}/scripts/setup_pinky.sh"
