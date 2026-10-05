#!/bin/sh
# Turn the ASAP7 HSPICE model cards into ngspice OSDI model cards.
#
#   ngspice/asap7/adapt-models.sh PDK_DIR OUT_DIR
#
# PDK_DIR is the pinned asap7_pdk_r1p7 checkout. Writes OUT_DIR/7nm_{TT,FF,SS}.pm
# and checks each against ngspice/asap7/adapted.sha256, so every host gets
# byte-identical cards. The one change is recorded in ngspice/ADAPTATIONS.md:
#
#   .model <name> nmos level = 72   ->   .model <name> bsimcmg devtype=1
#   .model <name> pmos level = 72   ->   .model <name> bsimcmg devtype=0
#
# Every parameter line is left exactly as upstream wrote it.
set -eu

pdk=$1
out=$2
here=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$out"
for c in TT FF SS; do
  sed -E \
    -e 's/^\.model ([a-z_]+) nmos level = 72 *$/.model \1 bsimcmg devtype=1/' \
    -e 's/^\.model ([a-z_]+) pmos level = 72 *$/.model \1 bsimcmg devtype=0/' \
    "$pdk/models/hspice/7nm_${c}_160803.pm" > "$out/7nm_$c.pm"
  n=$(grep -c '^\.model [a-z_]* bsimcmg devtype=[01]$' "$out/7nm_$c.pm")
  if [ "$n" != 8 ]; then
    echo "adapt-models.sh: expected 8 adapted .model lines in 7nm_$c.pm, got $n" >&2
    exit 1
  fi
done

cd "$out"
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c --quiet "$here/adapted.sha256"
else
  shasum -a 256 -c --quiet "$here/adapted.sha256"
fi
