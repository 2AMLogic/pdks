# SKY130 setup, sourced by bootstrap.sh (which provides the helpers).
# shellcheck shell=bash

# shellcheck source=pdks/sky130/upstream.lock
. "$REPO/pdks/sky130/upstream.lock"
# shellcheck disable=SC2034  # read by bootstrap.sh
NEED_ZSTD=1
GUARD_DIRS+=("$PREFIX/sky130")

setup_sky130() {
  local root="$PREFIX/sky130" ng="$PREFIX/sky130/ngspice"
  local id; id="sky130 $SKY130_COMMON_SHA256 $SKY130_FD_PR_SHA256 $(files_id "$REPO/pdks/sky130/setup.sh" "$REPO/ngspice/wire.inc" "$REPO/pdks/sky130/interconnect.csv" "$REPO"/ngspice/sky130/*.in)"
  if stamp_ok "$root" "$id"; then
    log "SKY130: already set up"
    return
  fi
  log "SKY130: fetching open_pdks $SKY130_OPEN_PDKS_COMMIT release (21 MB)"
  local common="$CACHE/sky130-$SKY130_OPEN_PDKS_COMMIT-common.tar.zst"
  local fdpr="$CACHE/sky130-$SKY130_OPEN_PDKS_COMMIT-sky130_fd_pr.tar.zst"
  fetch "$SKY130_URL_BASE/common.tar.zst" "$SKY130_COMMON_SHA256" "$common"
  fetch "$SKY130_URL_BASE/sky130_fd_pr.tar.zst" "$SKY130_FD_PR_SHA256" "$fdpr"
  claim_dir "$root"
  zstd -dc "$common" | tar -x -C "$root" sky130A/.config sky130A/libs.tech/ngspice sky130A/libs.tech/combined
  zstd -dc "$fdpr" | tar -x -C "$root" sky130A/libs.ref/sky130_fd_pr/spice
  # No adaptations: the library is ngspice-native (BSIM4, no OSDI).
  mkdir -p "$ng"
  local t
  for t in spiceinit example.sp; do
    render "$REPO/ngspice/sky130/$t.in" "$ng/$t" "PDK_DIR=$root/sky130A" "NGSPICE=$NGSPICE"
  done
  render "$REPO/ngspice/sky130/mismatch.sp.in" "$ng/mismatch.sp" "PDK_DIR=$root/sky130A" "NGSPICE=$NGSPICE" \
    CORNER=tt_mm W=1 L=0.5 M=1 N=100 SEED=1
  render "$REPO/ngspice/sky130/noise.sp.in" "$ng/noise.sp" "PDK_DIR=$root/sky130A" "NGSPICE=$NGSPICE" \
    W=7 L=8 VG=1.2 VD=0.9 VGLO=1.198 VGHI=1.202
  cp "$ng/spiceinit" "$ng/.spiceinit"
  log "SKY130: installing interconnect table and wire include"
  interconnect_inc sky130
  stamp "$root" "$id"
}
