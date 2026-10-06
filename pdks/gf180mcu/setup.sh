# GF180MCU setup, sourced by bootstrap.sh (which provides the helpers).
# shellcheck shell=bash

# shellcheck source=pdks/gf180mcu/upstream.lock
. "$REPO/pdks/gf180mcu/upstream.lock"
GUARD_DIRS+=("$PREFIX/gf180mcu")

setup_gf180mcu() {
  local root="$PREFIX/gf180mcu" ng="$PREFIX/gf180mcu/ngspice"
  local id; id="gf180mcu $GF180_FDPR_COMMIT $(files_id "$REPO/pdks/gf180mcu/setup.sh" "$REPO/pdks/gf180mcu/files.sha256" "$REPO"/ngspice/gf180mcu/*.in)"
  if stamp_ok "$root" "$id"; then
    log "GF180MCU: already set up"
    return
  fi
  log "GF180MCU: fetching device models at $GF180_FDPR_COMMIT"
  claim_dir "$root"
  local f sum
  while read -r sum f; do
    fetch "$GF180_FDPR_RAW/$f" "$sum" "$root/gf180mcu_fd_pr/$f"
  done < "$REPO/pdks/gf180mcu/files.sha256"
  # No adaptations: the cards are ngspice-native BSIM4.
  mkdir -p "$ng"
  render "$REPO/ngspice/gf180mcu/example.sp.in" "$ng/example.sp" \
    "MODELS_DIR=$root/gf180mcu_fd_pr/models/ngspice" "NGSPICE=$NGSPICE"
  stamp "$root" "$id"
}
