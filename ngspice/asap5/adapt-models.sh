#!/bin/sh
# Turn the ASAP5 HSPICE cards (one file per device per corner) into one
# ngspice OSDI card file per corner.
#
#   ngspice/asap5/adapt-models.sh MODELS_DIR OUT_DIR
#
# MODELS_DIR is asap5PDK_r0p4/models/hspice/allvt_cgp44_210623a/nwfet of the
# pinned checkout. Writes OUT_DIR/asap5_{TT,FF,SS,FS,SF}.pm and checks each
# against ngspice/asap5/adapted.sha256. Changes, recorded in
# ngspice/ADAPTATIONS.md:
#
#   A1  .model <name> nmos|pmos level = 72  ->  .model <name> bsimcmg devtype=1|0
#   A5  lrsd = 0      -> removed (BSIM-CMG's default, L; LRSD is unused at
#                         rgeomod = 0 and cgeomod = 0, as all 40 cards set)
#   A6  drout = 0.0   -> 1.06 (BSIM-CMG's default; DROUT has no effect when
#                         pdibl1 = 0, as all 40 cards set)
set -eu

src=$1
out=$2
here=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$out"
for c in TT FF SS FS SF; do
  lc=$(echo "$c" | tr 'A-Z' 'a-z')
  : > "$out/asap5_$c.pm"
  for d in nmos_sram nmos_rvt nmos_lvt nmos_slvt pmos_sram pmos_rvt pmos_lvt pmos_slvt; do
    sed -E \
      -e 's/^\.model ([a-z_]+) nmos level = 72 *$/.model \1 bsimcmg devtype=1/' \
      -e 's/^\.model ([a-z_]+) pmos level = 72 *$/.model \1 bsimcmg devtype=0/' \
      -e 's/^\+lrsd    = 0               /+/' \
      -e 's/drout   = 0\.0      /drout   = 1.06     /' \
      "$src/${d}_${lc}_hc_nwfet_asap5_210623a.pm" >> "$out/asap5_$c.pm"
  done
  for pat in '^\.model [a-z_]* bsimcmg devtype=[01]$' 'drout   = 1\.06'; do
    n=$(grep -c "$pat" "$out/asap5_$c.pm")
    [ "$n" = 8 ] || { echo "adapt-models.sh: expected 8 matches of '$pat' in asap5_$c.pm, got $n" >&2; exit 1; }
  done
  if grep -q 'lrsd' "$out/asap5_$c.pm"; then
    echo "adapt-models.sh: lrsd left in asap5_$c.pm" >&2; exit 1
  fi
done

cd "$out"
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c --quiet "$here/adapted.sha256"
else
  shasum -a 256 -c --quiet "$here/adapted.sha256"
fi
