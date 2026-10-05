#!/usr/bin/env bash
# Set up open PDKs for ngspice simulation on macOS or Linux.
#
#   ./bootstrap.sh --pdk asap7 [--prefix ~/pdks] [options]
#
# Fetches every pinned source (tools/versions.lock, pdks/<pdk>/upstream.lock),
# verifies it by SHA-256 or git commit, builds ngspice and the simulator
# models, applies the recorded adaptations (ngspice/ADAPTATIONS.md) and runs
# the sanity checks (sanity/). Safe to re-run: finished steps are skipped.
#
# Options:
#   --pdk NAME          PDK to set up (supported: asap7). Required.
#   --prefix DIR        Install root (default: ~/pdks).
#   --jobs N            Parallel build jobs (default: CPU count).
#   --no-prereqs        Don't try to install system packages (apt-get only).
#   --skip-sanity       Don't run the sanity checks at the end.
#   -h, --help          Show this help.
#
# Layout under the prefix:
#   tools/ngspice-<ver>/        ngspice, built with OSDI (tools/ngspice -> it)
#   tools/openvaf-r-<ver>/      OpenVAF-reloaded compiler
#   tools/bsimcmg107/           BSIM-CMG source, prepared source, .osdi
#   asap7/asap7_pdk_r1p7/       upstream PDK at the pinned commit
#   asap7/ngspice/              adapted model cards, asap7.lib, spiceinit
#   env.sh                      source this to put ngspice on PATH
#
# Every directory this script creates carries a .bootstrap-stamp file. It
# refuses to write into an existing directory without one, so it never
# overwrites an install made some other way.

set -euo pipefail

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PDK=""
PREFIX="$HOME/pdks"
JOBS=""
PREREQS=1
SANITY=1

usage() { sed -n '2,/^$/s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"; }
log() { printf '\033[1m==> %s\033[0m\n' "$*"; }
die() { printf 'bootstrap: %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case $1 in
    --pdk) PDK=${2:?--pdk needs a value}; shift 2 ;;
    --pdk=*) PDK=${1#*=}; shift ;;
    --prefix) PREFIX=${2:?--prefix needs a value}; shift 2 ;;
    --prefix=*) PREFIX=${1#*=}; shift ;;
    --jobs) JOBS=${2:?--jobs needs a value}; shift 2 ;;
    --no-prereqs) PREREQS=0; shift ;;
    --skip-sanity) SANITY=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
done

case $PDK in
  asap7) ;;
  "") die "--pdk is required (supported: asap7)" ;;
  *) die "unsupported PDK: $PDK (supported: asap7)" ;;
esac

case $PREFIX in /*) ;; *) PREFIX="$PWD/$PREFIX" ;; esac
TOOLS="$PREFIX/tools"
CACHE="$PREFIX/.cache"

# shellcheck source=tools/versions.lock
. "$REPO/tools/versions.lock"
# shellcheck source=pdks/asap7/upstream.lock
. "$REPO/pdks/asap7/upstream.lock"

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

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
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
}
stamp() { printf '%s' "$2" > "$1/.bootstrap-stamp"; }

fetch() { # url sha256 dest
  if [ -f "$3" ] && [ "$(sha256 "$3")" = "$2" ]; then return; fi
  mkdir -p "$(dirname "$3")"
  curl -fsSL --retry 3 -o "$3.part" "$1"
  local got; got=$(sha256 "$3.part")
  [ "$got" = "$2" ] || { rm -f "$3.part"; die "checksum mismatch for $1: got $got, expected $2"; }
  mv "$3.part" "$3"
}

# --- prerequisites ------------------------------------------------------------

prereqs() {
  log "Checking prerequisites"
  local missing=()
  for c in curl git make tar python3; do command -v "$c" >/dev/null 2>&1 || missing+=("$c"); done
  command -v cc >/dev/null 2>&1 || command -v gcc >/dev/null 2>&1 || missing+=("cc")
  command -v bison >/dev/null 2>&1 || missing+=("bison")
  command -v flex >/dev/null 2>&1 || missing+=("flex")
  if [ "$OS" = Linux ] && ! ldconfig -p 2>/dev/null | grep -q 'libLLVM.so.18.1\|libLLVM-18.so'; then
    missing+=("libLLVM-18")
  fi
  [ ${#missing[@]} -eq 0 ] && return

  if [ "$OS" = Darwin ]; then
    die "missing: ${missing[*]}. Install the Xcode Command Line Tools (xcode-select --install); bison and flex ship with them"
  fi
  if [ "$PREREQS" = 1 ] && command -v apt-get >/dev/null 2>&1; then
    local sudo=""
    [ "$(id -u)" = 0 ] || sudo="sudo"
    log "Installing system packages with apt-get (missing: ${missing[*]})"
    $sudo apt-get update -qq
    $sudo apt-get install -y -qq build-essential bison flex curl git python3 libllvm18
    return
  fi
  die "missing: ${missing[*]}. On Debian/Ubuntu: apt-get install build-essential bison flex curl git python3 libllvm18"
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

# --- BSIM-CMG 107 -> .osdi ---------------------------------------------------------

build_bsimcmg() {
  local dir="$TOOLS/bsimcmg107"
  local id; id="bsimcmg $BSIMCMG_URL_BASE $(sha256 "$REPO/tools/bsimcmg107.sha256") $(sha256 "$REPO/ngspice/bsimcmg107/prepare.sh") openvaf-r $OPENVAF_VERSION"
  OSDI="$dir/bsimcmg107.osdi"
  if stamp_ok "$dir" "$id" && [ -f "$OSDI" ]; then
    log "BSIM-CMG $BSIMCMG_VERSION OSDI: already built"
    return
  fi
  log "BSIM-CMG $BSIMCMG_VERSION: fetching, preparing and compiling to OSDI"
  claim_dir "$dir"
  mkdir -p "$dir/src"
  local f sum
  while read -r sum f; do
    fetch "$BSIMCMG_URL_BASE/$f" "$sum" "$dir/src/$f"
  done < "$REPO/tools/bsimcmg107.sha256"
  "$REPO/ngspice/bsimcmg107/prepare.sh" "$dir/src" "$dir/osdi-src"
  (cd "$dir/osdi-src" && "$OPENVAF" bsimcmg.va -o "$OSDI" >"$dir/openvaf.log" 2>&1) \
    || { tail -30 "$dir/openvaf.log"; die "OpenVAF failed to compile BSIM-CMG"; }
  stamp "$dir" "$id"
}

# --- ASAP7 ---------------------------------------------------------------------------

setup_asap7() {
  local root="$PREFIX/asap7" pdk="$PREFIX/asap7/asap7_pdk_r1p7" ng="$PREFIX/asap7/ngspice"
  local id; id="asap7 $ASAP7_PDK_COMMIT $(cat "$REPO/pdks/asap7/models.sha256" "$REPO/ngspice/asap7/adapted.sha256" "$REPO"/ngspice/asap7/*.in | sha256 /dev/stdin)"
  if stamp_ok "$root" "$id" && [ -d "$pdk" ] && [ "$(git -C "$pdk" rev-parse HEAD)" = "$ASAP7_PDK_COMMIT" ]; then
    log "ASAP7 r1p7: already set up"
    return
  fi
  log "ASAP7 r1p7: fetching $ASAP7_PDK_COMMIT"
  claim_dir "$root"
  git init -q "$pdk"
  git -C "$pdk" remote add origin "$ASAP7_PDK_URL"
  git -C "$pdk" fetch -q --depth 1 origin "$ASAP7_PDK_COMMIT"
  git -C "$pdk" -c advice.detachedHead=false checkout -q FETCH_HEAD
  [ "$(git -C "$pdk" rev-parse HEAD)" = "$ASAP7_PDK_COMMIT" ] || die "ASAP7 checkout is not at $ASAP7_PDK_COMMIT"
  if command -v sha256sum >/dev/null 2>&1; then
    (cd "$pdk" && sha256sum -c --quiet "$REPO/pdks/asap7/models.sha256")
  else
    (cd "$pdk" && shasum -a 256 -c --quiet "$REPO/pdks/asap7/models.sha256")
  fi

  log "ASAP7 r1p7: adapting model cards for ngspice"
  "$REPO/ngspice/asap7/adapt-models.sh" "$pdk" "$ng/models"
  local t
  for t in asap7.lib spiceinit example.sp; do
    sed -e "s|@MODELS_DIR@|$ng/models|g" -e "s|@OSDI@|$OSDI|g" -e "s|@NGSPICE@|$NGSPICE|g" \
      "$REPO/ngspice/asap7/$t.in" > "$ng/$t"
  done
  mv "$ng/asap7.lib" "$ng/models/asap7.lib"
  stamp "$root" "$id"
}

write_env() {
  cat > "$PREFIX/env.sh" <<EOF
# Generated by bootstrap.sh. Source it:  . "$PREFIX/env.sh"
export PATH="$TOOLS/ngspice/bin:\$PATH"
export PDK_ROOT="$PREFIX"
export ASAP7_NGSPICE="$PREFIX/asap7/ngspice"
export BSIMCMG_OSDI="$TOOLS/bsimcmg107/bsimcmg107.osdi"
EOF
}

# --- main ----------------------------------------------------------------------------

for d in "$TOOLS/ngspice-$NGSPICE_VERSION" "$TOOLS/openvaf-r-$OPENVAF_VERSION" \
         "$TOOLS/bsimcmg107" "$PREFIX/asap7"; do
  if [ -e "$d" ] && [ ! -f "$d/.bootstrap-stamp" ]; then
    die "$d exists and was not created by bootstrap.sh; move it aside or choose another --prefix"
  fi
done
mkdir -p "$PREFIX" "$TOOLS" "$CACHE"
prereqs
build_ngspice
install_openvaf
build_bsimcmg
setup_asap7
write_env

log "Smoke test: $PREFIX/asap7/ngspice/example.sp"
(cd "$PREFIX/asap7/ngspice" && "$NGSPICE" -b -n example.sp 2>&1 | grep -E '^vm ' ) \
  || die "example deck failed"

if [ "$SANITY" = 1 ]; then
  log "Sanity checks (sanity/run.py)"
  python3 "$REPO/sanity/run.py" --prefix "$PREFIX" --json "$PREFIX/asap7/sanity-results.json"
fi

log "Done. Source $PREFIX/env.sh, then see $PREFIX/asap7/ngspice/example.sp"
