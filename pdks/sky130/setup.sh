# SKY130 setup, sourced by bootstrap.sh (which provides the helpers).
# shellcheck shell=bash

# shellcheck source=pdks/sky130/upstream.lock
. "$REPO/pdks/sky130/upstream.lock"
# shellcheck disable=SC2034  # read by bootstrap.sh
NEED_ZSTD=1
GUARD_DIRS+=("$PREFIX/sky130")

setup_sky130() {
  local root="$PREFIX/sky130" ng="$PREFIX/sky130/ngspice"
  local id; id="sky130 $SKY130_COMMON_SHA256 $SKY130_FD_PR_SHA256 $(files_id "$REPO"/ngspice/sky130/*.in)"
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
  zstd -dc "$common" | tar -x -C "$root" sky130A/.config sky130A/libs.tech/ngspice
  zstd -dc "$fdpr" | tar -x -C "$root" sky130A/libs.ref/sky130_fd_pr/spice
  # No adaptations: the library is ngspice-native (BSIM4, no OSDI).
  mkdir -p "$ng"
  local t
  for t in spiceinit example.sp; do
    render "$REPO/ngspice/sky130/$t.in" "$ng/$t" "PDK_DIR=$root/sky130A" "NGSPICE=$NGSPICE"
  done
  cp "$ng/spiceinit" "$ng/.spiceinit"
  stamp "$root" "$id"
}
