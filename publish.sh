#!/usr/bin/env bash
# this_file: publish.sh
# Release vexy-glob: tag the next vX.Y.Z and let CI build and upload the wheels.
#
# maturin takes the package version from Cargo.toml, not from the git tag, and
# a local build only yields a wheel for this machine. So this script:
#   1. computes the next tag the same way gitnextver does (highest vX.Y.Z tag,
#      patch + 1),
#   2. writes that version into Cargo.toml,
#   3. builds and checks the sdist and a local wheel as a pre-flight test,
#   4. runs `uvx gitnextver`, which commits all pending changes, tags vX.Y.Z
#      and pushes the commit and the tag,
#   5. checks that the new tag is the one computed in step 1.
# The tag push starts .github/workflows/release.yml, which verifies that the
# tag matches Cargo.toml, builds the Linux/macOS/Windows wheels and the sdist,
# and uploads them to PyPI. Nothing is uploaded from this machine.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

die() { echo "publish.sh: $*" >&2; exit 1; }

git fetch --tags --quiet origin
if upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)"; then
  behind="$(git rev-list --count "HEAD..${upstream}")"
  [[ "$behind" == 0 ]] || die "branch is ${behind} commit(s) behind ${upstream}; pull first."
fi

last="$(git tag --list 'v*' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n 1 || true)"
if [[ -z "$last" ]]; then
  next="1.0.0"
else
  IFS=. read -r major minor patch <<<"${last#v}"
  next="${major}.${minor}.$((patch + 1))"
fi
tag="v${next}"
git rev-parse -q --verify "refs/tags/${tag}" >/dev/null && die "tag ${tag} already exists."
echo "Last tag: ${last:-none}. Releasing ${tag}."

# Only the first `version = "..."` line, which is the [package] version.
perl -0pi -e "s/^version = \"[^\"]*\"/version = \"${next}\"/m" Cargo.toml
grep -q "^version = \"${next}\"$" Cargo.toml || die "could not set the version in Cargo.toml."

./build.sh package

uvx gitnextver
made="$(git describe --tags --exact-match HEAD 2>/dev/null || true)"
if [[ "$made" != "$tag" ]]; then
  die "expected HEAD to carry ${tag}, found '${made:-no tag}'. Cargo.toml says ${next}; fix the tag or Cargo.toml before CI publishes."
fi
echo "Pushed ${tag}. GitHub Actions (release.yml) now builds the wheels and uploads them to PyPI."
