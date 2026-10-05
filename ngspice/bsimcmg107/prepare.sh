#!/bin/sh
# Prepare the pristine BSIM-CMG 107.0.0 Verilog-A for OpenVAF/ngspice.
#
#   ngspice/bsimcmg107/prepare.sh SRC_DIR OUT_DIR
#
# SRC_DIR holds the 12 upstream files (checked against tools/bsimcmg107.sha256
# by bootstrap.sh). OUT_DIR receives a copy with the two edits recorded in
# ngspice/ADAPTATIONS.md, and the result is verified by SHA-256 so the
# compiled model is the same on every host. This script carries the edits,
# not any of the Berkeley source.
set -eu

src=$1
out=$2
expected=f060d3c26330493faf91d0aee41367cbe29a119e63c58a4d44112b792f38fa38

rm -rf "$out"
mkdir -p "$out"
cp "$src"/*.va "$src"/*.include "$out"/

# Edit 1: tag the per-instance parameters (BSIM-CMG 107 manual, instance
# parameter table) so OpenVAF exposes them as OSDI instance parameters.
# Without this, L, NFIN, NF, ... are model-only and cannot be set per device.
script="$out/.prepare.sed"
: > "$script"
for p in L D TFIN FPITCH NF NFIN NGCON ASEO ADEO PSEO PDEO ASEJ ADEJ PSEJ PDEJ \
         COVS COVD CGSP CGDP CDSP NRS NRD LRSD DTEMP DELVTRAND U0MULT; do
  printf 's/^([[:space:]]*)parameter (real|integer)([[:space:]]+)%s([[:space:]]*=)/\\1(*type="instance"*) parameter \\2\\3%s\\4/\n' "$p" "$p" >> "$script"
done
sed -E -f "$script" "$src/bsimcmg_body.include" > "$out/bsimcmg_body.include.tmp"
rm "$script"

# Edit 2: write the lower bound of EOTACC as 1e-10 instead of 0.1n. OpenVAF
# evaluates 0.1n as 0.1 * 1e-9, one ulp above 1e-10, so the ASAP7 cards'
# eotacc = 1e-10 (the bound value, legal in the spec) is rejected as out of
# bounds and ngspice aborts model setup.
sed 's/^parameter real EOTACC    =  EOT from \[0\.1n:inf);/parameter real EOTACC    =  EOT from [1e-10:inf);/' \
  "$out/bsimcmg_body.include.tmp" > "$out/bsimcmg_body.include"
rm "$out/bsimcmg_body.include.tmp"

if command -v sha256sum >/dev/null 2>&1; then
  got=$(sha256sum "$out/bsimcmg_body.include" | cut -d' ' -f1)
else
  got=$(shasum -a 256 "$out/bsimcmg_body.include" | cut -d' ' -f1)
fi
if [ "$got" != "$expected" ]; then
  echo "prepare.sh: patched bsimcmg_body.include has SHA-256 $got, expected $expected" >&2
  exit 1
fi
