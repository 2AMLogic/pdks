# ASAP5 r0p4 setup, sourced by bootstrap.sh (which provides the helpers).
# shellcheck shell=bash

# shellcheck source=pdks/asap5/upstream.lock
. "$REPO/pdks/asap5/upstream.lock"
# shellcheck disable=SC2034  # read by bootstrap.sh
NEED_OPENVAF=1
GUARD_DIRS+=("$TOOLS/bsimcmg107" "$PREFIX/asap5")
# shellcheck source=pdks/bsimcmg.sh
. "$REPO/pdks/bsimcmg.sh"

setup_asap5() {
  build_bsimcmg
  local root="$PREFIX/asap5" pdk="$PREFIX/asap5/asap5" ng="$PREFIX/asap5/ngspice"
  local id; id="asap5 $ASAP5_COMMIT $(files_id "$REPO/pdks/asap5/setup.sh" "$REPO/pdks/asap5/models.sha256" "$REPO/ngspice/asap5/adapted.sha256" "$REPO"/ngspice/asap5/*.in)"
  if stamp_ok "$root" "$id"; then
    log "ASAP5 r0p4: already set up"
    return
  fi
  log "ASAP5 r0p4: fetching $ASAP5_COMMIT (models only)"
  claim_dir "$root"
  git_pinned "$ASAP5_URL" "$ASAP5_COMMIT" "$pdk" /LICENSE "/$ASAP5_MODELS/"
  check_sums "$pdk" "$REPO/pdks/asap5/models.sha256"

  log "ASAP5 r0p4: adapting model cards for ngspice"
  "$REPO/ngspice/asap5/adapt-models.sh" "$pdk/$ASAP5_MODELS" "$ng/models"
  local t
  for t in asap5.lib spiceinit example.sp; do
    render "$REPO/ngspice/asap5/$t.in" "$ng/$t" \
      "MODELS_DIR=$ng/models" "OSDI=$BSIMCMG_OSDI" "NGSPICE=$NGSPICE"
  done
  mv "$ng/asap5.lib" "$ng/models/asap5.lib"
  stamp "$root" "$id"
}
