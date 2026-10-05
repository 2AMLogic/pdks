#!/usr/bin/env bash
# Set up open PDKs for ngspice simulation on macOS or Linux.
#
#   ./bootstrap.sh --pdk NAME[,NAME...] [--prefix ~/pdks] [options]
#
# PDKs: asap7, sky130, gf180mcu, ihp-sg13g2, ihp-sg13cmos5l, or "all".
#
# Fetches every pinned source (tools/versions.lock, pdks/<pdk>/upstream.lock),
# verifies it by SHA-256 or git commit, builds ngspice and any Verilog-A
# models the PDK needs, applies the recorded adaptations
# (ngspice/ADAPTATIONS.md) and runs the sanity checks (sanity/<pdk>/).
# Safe to re-run: finished steps are skipped.
#
# Options:
#   --pdk LIST          PDKs to set up, comma-separated or repeated. Required.
#   --prefix DIR        Install root (default: ~/pdks).
#   --jobs N            Parallel build jobs (default: CPU count).
#   --no-prereqs        Don't try to install system packages.
#   --skip-sanity       Don't run the sanity checks at the end.
#   -h, --help          Show this help.
#
# Layout under the prefix:
#   tools/ngspice-<ver>/        ngspice, built with OSDI (tools/ngspice -> it)
#   tools/openvaf-r-<ver>/      OpenVAF-reloaded (only if a PDK needs OSDI)
#   <pdk>/                      pinned upstream files for that PDK
#   <pdk>/ngspice/              spiceinit, example.sp, and any adapted models
#   env.sh                      source this to put ngspice on PATH
#
# Every directory this script creates carries a .bootstrap-stamp file. It
# refuses to write into an existing directory without one, so it never
# overwrites an install made some other way.

set -euo pipefail

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALL_PDKS="asap7 sky130 gf180mcu ihp-sg13g2 ihp-sg13cmos5l"
PDKS=""
PREFIX="$HOME/pdks"
JOBS=""
PREREQS=1
SANITY=1

usage() { sed -n '2,/^$/s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"; }
log() { printf '\033[1m==> %s\033[0m\n' "$*"; }
die() { printf 'bootstrap: %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case $1 in
    --pdk) PDKS="$PDKS ${2:?--pdk needs a value}"; shift 2 ;;
    --pdk=*) PDKS="$PDKS ${1#*=}"; shift ;;
    --prefix) PREFIX=${2:?--prefix needs a value}; shift 2 ;;
    --prefix=*) PREFIX=${1#*=}; shift ;;
    --jobs) JOBS=${2:?--jobs needs a value}; shift 2 ;;
    --no-prereqs) PREREQS=0; shift ;;
    --skip-sanity) SANITY=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
done

PDKS=$(echo "$PDKS" | tr ',' ' ')
[ -n "${PDKS// /}" ] || die "--pdk is required (one or more of: $ALL_PDKS, or all)"
case " $PDKS " in *" all "*) PDKS=$ALL_PDKS ;; esac
for p in $PDKS; do
  case " $ALL_PDKS " in *" $p "*) ;; *) die "unsupported PDK: $p (supported: $ALL_PDKS)" ;; esac
done

case $PREFIX in /*) ;; *) PREFIX="$PWD/$PREFIX" ;; esac
TOOLS="$PREFIX/tools"
CACHE="$PREFIX/.cache"

# shellcheck source=tools/versions.lock
. "$REPO/tools/versions.lock"

# --- platform -----------------------------------------------------------------

OS=$(uname -s)
ARCH=$(uname -m)
case "$OS/$ARCH" in
  Darwin/arm64) PLAT=macos_aarch64 ;;
  Darwin/x86_64) PLAT=macos_x86_64 ;;
  Linux/x86_64) PLAT=linux_x86_64 ;;
  *) die "unsupported platform $OS/$ARCH (OpenVAF-reloaded publishes Linux x86_64 and macOS)" ;;
esac
if [ -z "$JOBS" ]; then
  JOBS=$(getconf _NPROCESSORS_ONLN 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
fi

# --- helpers used by pdks/<pdk>/setup.sh ----------------------------------------

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

# check_sums DIR FILE: verify a "sha256  path" list relative to DIR
check_sums() {
  if command -v sha256sum >/dev/null 2>&1; then (cd "$1" && sha256sum -c --quiet "$2")
  else (cd "$1" && shasum -a 256 -c --quiet "$2"); fi
}

# A directory is ours if it has a stamp; its content is current if the stamp
# matches. Refuse to touch a directory that exists without a stamp.
stamp_ok() { [ -f "$1/.bootstrap-stamp" ] && [ "$(cat "$1/.bootstrap-stamp")" = "$2" ]; }
claim_dir() {
  if [ -e "$1" ] && [ ! -f "$1/.bootstrap-stamp" ]; then
    die "$1 exists and was not created by bootstrap.sh; move it aside or choose another --prefix"
  fi
  rm -rf "$1"
  mkdir -p "$1"
  # Mark it ours at once, so a run that fails part-way can be resumed; the
  # real stamp replaces this only when the step completes.
  printf 'incomplete' > "$1/.bootstrap-stamp"
}
stamp() { printf '%s' "$2" > "$1/.bootstrap-stamp"; }

# A stamp id that changes when any of the given repo files change
files_id() { cat "$@" | sha256 /dev/stdin; }

fetch() { # url sha256 dest
  if [ -f "$3" ] && [ "$(sha256 "$3")" = "$2" ]; then return; fi
  mkdir -p "$(dirname "$3")"
  curl -fsSL --retry 5 --retry-delay 2 --retry-all-errors -o "$3.part" "$1"
  local got; got=$(sha256 "$3.part")
  [ "$got" = "$2" ] || { rm -f "$3.part"; die "checksum mismatch for $1: got $got, expected $2"; }
  mv "$3.part" "$3"
}

# git_pinned URL COMMIT DIR [SPARSE_PATH...]: shallow-fetch exactly COMMIT
# into DIR, optionally checking out only the given paths, and verify HEAD.
git_pinned() {
  local url=$1 commit=$2 dir=$3; shift 3
  git init -q "$dir"
  git -C "$dir" remote add origin "$url"
  if [ $# -gt 0 ]; then
    git -C "$dir" sparse-checkout set --no-cone "$@"
    git -C "$dir" fetch -q --depth 1 --filter=blob:none origin "$commit"
  else
    git -C "$dir" fetch -q --depth 1 origin "$commit"
  fi
  git -C "$dir" -c advice.detachedHead=false checkout -q FETCH_HEAD
  [ "$(git -C "$dir" rev-parse HEAD)" = "$commit" ] || die "$dir is not at $commit"
}

# render SRC DST KEY=VALUE...: copy a template, replacing @KEY@ with VALUE
render() {
  local src=$1 dst=$2; shift 2
  local args=() kv
  for kv in "$@"; do args+=(-e "s|@${kv%%=*}@|${kv#*=}|g"); done
  sed "${args[@]}" "$src" > "$dst"
}

# --- per-PDK modules ------------------------------------------------------------

# Each pdks/<pdk>/setup.sh defines setup_<pdk with - as _> and may set:
#   NEED_OPENVAF=1   the PDK compiles Verilog-A to OSDI
#   NEED_ZSTD=1      the PDK's pinned release is a .tar.zst
# and append to GUARD_DIRS the directories it will create.
NEED_OPENVAF=0
NEED_ZSTD=0
GUARD_DIRS=("$TOOLS/ngspice-$NGSPICE_VERSION")
for p in $PDKS; do
  # shellcheck source=/dev/null
  . "$REPO/pdks/$p/setup.sh"
done
[ "$NEED_OPENVAF" = 1 ] && GUARD_DIRS+=("$TOOLS/openvaf-r-$OPENVAF_VERSION")

# --- prerequisites ------------------------------------------------------------

prereqs() {
  log "Checking prerequisites"
  local missing=() c
  for c in curl git make tar python3 bison flex; do command -v "$c" >/dev/null 2>&1 || missing+=("$c"); done
  command -v cc >/dev/null 2>&1 || command -v gcc >/dev/null 2>&1 || missing+=("cc")
  if [ "$NEED_ZSTD" = 1 ] && ! command -v zstd >/dev/null 2>&1; then missing+=("zstd"); fi
  if [ "$NEED_OPENVAF" = 1 ] && [ "$OS" = Linux ] \
     && ! ldconfig -p 2>/dev/null | grep -q 'libLLVM.so.18.1\|libLLVM-18.so'; then
    missing+=("libLLVM-18")
  fi
  [ ${#missing[@]} -eq 0 ] && return

  if [ "$OS" = Darwin ]; then
    if [ "${missing[*]}" = zstd ] && [ "$PREREQS" = 1 ] && command -v brew >/dev/null 2>&1; then
      log "Installing zstd with Homebrew"
      brew install zstd
      return
    fi
    die "missing: ${missing[*]}. Install the Xcode Command Line Tools (xcode-select --install; bison and flex ship with them), and zstd (brew install zstd) for sky130"
  fi
  if [ "$PREREQS" = 1 ] && command -v apt-get >/dev/null 2>&1; then
    local sudo=""
    [ "$(id -u)" = 0 ] || sudo="sudo"
    log "Installing system packages with apt-get (missing: ${missing[*]})"
    $sudo apt-get update -qq
    $sudo apt-get install -y -qq build-essential bison flex curl git python3 zstd libllvm18
    return
  fi
  die "missing: ${missing[*]}. On Debian/Ubuntu: apt-get install build-essential bison flex curl git python3 zstd libllvm18"
}

# --- ngspice --------------------------------------------------------------------

build_ngspice() {
  local dir="$TOOLS/ngspice-$NGSPICE_VERSION" id="ngspice $NGSPICE_VERSION $NGSPICE_SHA256"
  if stamp_ok "$dir" "$id" && [ -x "$dir/bin/ngspice" ]; then
    log "ngspice $NGSPICE_VERSION: already built"
  else
    log "ngspice $NGSPICE_VERSION: fetching and building (a few minutes)"
    local tgz="$CACHE/ngspice-$NGSPICE_VERSION.tar.gz" build="$CACHE/build/ngspice-$NGSPICE_VERSION"
    fetch "$NGSPICE_URL" "$NGSPICE_SHA256" "$tgz"
    claim_dir "$dir"
    rm -rf "$build"; mkdir -p "$build"
    tar -xzf "$tgz" -C "$build" --strip-components 1
    # OSDI on, no X11/readline/OpenMP: a batch simulator with the fewest
    # host dependencies. OpenMP is off because Apple clang has no omp.h.
    (cd "$build" && ./configure --prefix="$dir" --enable-osdi --with-x=no \
        --with-readline=no --disable-openmp --disable-debug >"$build/configure.log" 2>&1 \
      || { tail -30 "$build/configure.log"; exit 1; })
    (cd "$build" && make -j"$JOBS" >"$build/make.log" 2>&1 || { tail -30 "$build/make.log"; exit 1; })
    (cd "$build" && make install >"$build/install.log" 2>&1)
    stamp "$dir" "$id"
    rm -rf "$build"
  fi
  ln -sfn "ngspice-$NGSPICE_VERSION" "$TOOLS/ngspice"
  NGSPICE="$TOOLS/ngspice/bin/ngspice"
}

# --- OpenVAF-reloaded -------------------------------------------------------------

install_openvaf() {
  local name="openvaf-r-$OPENVAF_VERSION-${PLAT/_/-}"
  local var="OPENVAF_SHA256_$PLAT"; local want=${!var}
  local dir="$TOOLS/openvaf-r-$OPENVAF_VERSION" id="openvaf-r $OPENVAF_VERSION $want"
  OPENVAF="$dir/bin/openvaf-r"
  if stamp_ok "$dir" "$id" && [ -x "$OPENVAF" ]; then
    log "OpenVAF-reloaded $OPENVAF_VERSION: already installed"
    return
  fi
  log "OpenVAF-reloaded $OPENVAF_VERSION: fetching ($PLAT)"
  local tgz="$CACHE/$name.tar.gz"
  fetch "$OPENVAF_URL_BASE/$name.tar.gz" "$want" "$tgz"
  claim_dir "$dir"
  tar -xzf "$tgz" -C "$dir" --strip-components 1
  if [ "$OS" = Darwin ]; then
    # The release binaries carry linker-only signatures that macOS kills on
    # launch (exit 137). An ad-hoc re-sign changes no code.
    codesign --force --sign - "$dir"/lib/*.dylib "$OPENVAF" >/dev/null 2>&1
  fi
  "$OPENVAF" --version >/dev/null || die "openvaf-r does not run on this host (on Linux it needs libLLVM 18)"
  stamp "$dir" "$id"
}

# compile_va VA OSDI [OPENVAF_ARGS...]: one Verilog-A file to one .osdi
compile_va() {
  local va=$1 out=$2; shift 2
  (cd "$(dirname "$va")" && "$OPENVAF" "$@" -o "$out" "$(basename "$va")" >"$out.log" 2>&1) \
    || { tail -30 "$out.log"; die "OpenVAF failed to compile $va"; }
  rm -f "$out.log"
}

write_env() {
  {
    echo "# Generated by bootstrap.sh. Source it:  . \"$PREFIX/env.sh\""
    echo "export PATH=\"$TOOLS/ngspice/bin:\$PATH\""
    echo "export PDK_ROOT=\"$PREFIX\""
    local p
    for p in "$PREFIX"/*/ngspice; do
      [ -d "$p" ] || continue
      p=${p%/ngspice}; p=${p##*/}
      echo "export $(echo "$p" | tr 'a-z-' 'A-Z_')_NGSPICE=\"$PREFIX/$p/ngspice\""
    done
  } > "$PREFIX/env.sh"
}

# --- main ----------------------------------------------------------------------------

for d in "${GUARD_DIRS[@]}"; do
  if [ -e "$d" ] && [ ! -f "$d/.bootstrap-stamp" ]; then
    die "$d exists and was not created by bootstrap.sh; move it aside or choose another --prefix"
  fi
done
mkdir -p "$PREFIX" "$TOOLS" "$CACHE"
prereqs
build_ngspice
[ "$NEED_OPENVAF" = 1 ] && install_openvaf
for p in $PDKS; do
  "setup_${p//-/_}"
done
write_env

status=0
for p in $PDKS; do
  log "$p: smoke test ($PREFIX/$p/ngspice/example.sp)"
  # A PDK that needs ngspice settings ships them as ngspice/.spiceinit,
  # which ngspice reads from the run directory in place of ~/.spiceinit.
  # Without one, -n keeps the user's ~/.spiceinit out of the test.
  nflag=-n; [ -f "$PREFIX/$p/ngspice/.spiceinit" ] && nflag=""
  # shellcheck disable=SC2086
  (cd "$PREFIX/$p/ngspice" && "$NGSPICE" -b $nflag example.sp 2>&1 | grep '^RESULT') \
    || die "$p: example deck failed"
  if [ "$SANITY" = 1 ]; then
    log "$p: sanity checks (sanity/$p/)"
    python3 "$REPO/sanity/run.py" --pdk "$p" --prefix "$PREFIX" \
      --json "$PREFIX/$p/sanity-results.json" || status=1
  fi
done

[ "$status" = 0 ] || die "sanity checks failed (see above)"
log "Done. Source $PREFIX/env.sh, then see $PREFIX/<pdk>/ngspice/example.sp"
