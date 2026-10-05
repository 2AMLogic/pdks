# Tokai Rika TR-1um setup, sourced by bootstrap.sh (which provides the helpers).
# shellcheck shell=bash

# shellcheck source=pdks/tr1um/upstream.lock
. "$REPO/pdks/tr1um/upstream.lock"
GUARD_DIRS+=("$PREFIX/tr1um")

setup_tr1um() {
  local root="$PREFIX/tr1um" ng="$PREFIX/tr1um/ngspice"
  local id; id="tr1um $TR1UM_COMMIT $(files_id "$REPO/pdks/tr1um/files.sha256" "$REPO"/ngspice/tr1um/*.in)"
  if stamp_ok "$root" "$id"; then
    log "TR-1um: already set up"
    return
  fi
  log "TR-1um: fetching SPICE models at $TR1UM_COMMIT"
  claim_dir "$root"
  local f sum
  while read -r sum f; do
    fetch "$TR1UM_RAW/$f" "$sum" "$root/TR-1um/$f"
  done < "$REPO/pdks/tr1um/files.sha256"
  # No adaptations for the MOSFETs: they load in ngspice unchanged.
  mkdir -p "$ng"
  render "$REPO/ngspice/tr1um/example.sp.in" "$ng/example.sp" \
    "MODELS_DIR=$root/TR-1um/libs.tech/spice/models" "NGSPICE=$NGSPICE"
  stamp "$root" "$id"
}
