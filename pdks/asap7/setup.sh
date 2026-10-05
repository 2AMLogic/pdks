# ASAP7 r1p7 setup, sourced by bootstrap.sh (which provides the helpers).
# shellcheck shell=bash

# shellcheck source=pdks/asap7/upstream.lock
. "$REPO/pdks/asap7/upstream.lock"
# shellcheck disable=SC2034  # read by bootstrap.sh
NEED_OPENVAF=1
GUARD_DIRS+=("$TOOLS/bsimcmg107" "$PREFIX/asap7")

# BSIM-CMG 107 Verilog-A -> .osdi (ASAP7's cards are BSIM-CMG 107)
build_bsimcmg() {
  local dir="$TOOLS/bsimcmg107"
  local id; id="bsimcmg $BSIMCMG_URL_BASE $(sha256 "$REPO/tools/bsimcmg107.sha256") $(sha256 "$REPO/ngspice/bsimcmg107/prepare.sh") openvaf-r $OPENVAF_VERSION"
  BSIMCMG_OSDI="$dir/bsimcmg107.osdi"
  if stamp_ok "$dir" "$id" && [ -f "$BSIMCMG_OSDI" ]; then
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
  compile_va "$dir/osdi-src/bsimcmg.va" "$BSIMCMG_OSDI"
  stamp "$dir" "$id"
}

setup_asap7() {
  build_bsimcmg
  local root="$PREFIX/asap7" pdk="$PREFIX/asap7/asap7_pdk_r1p7" ng="$PREFIX/asap7/ngspice"
  local id; id="asap7 $ASAP7_PDK_COMMIT $(files_id "$REPO/pdks/asap7/models.sha256" "$REPO/ngspice/asap7/adapted.sha256" "$REPO"/ngspice/asap7/*.in)"
  if stamp_ok "$root" "$id" && [ "$(git -C "$pdk" rev-parse HEAD 2>/dev/null)" = "$ASAP7_PDK_COMMIT" ]; then
    log "ASAP7 r1p7: already set up"
    return
  fi
  log "ASAP7 r1p7: fetching $ASAP7_PDK_COMMIT"
  claim_dir "$root"
  git_pinned "$ASAP7_PDK_URL" "$ASAP7_PDK_COMMIT" "$pdk"
  check_sums "$pdk" "$REPO/pdks/asap7/models.sha256"

  log "ASAP7 r1p7: adapting model cards for ngspice"
  "$REPO/ngspice/asap7/adapt-models.sh" "$pdk" "$ng/models"
  local t
  for t in asap7.lib spiceinit example.sp; do
    render "$REPO/ngspice/asap7/$t.in" "$ng/$t" \
      "MODELS_DIR=$ng/models" "OSDI=$BSIMCMG_OSDI" "NGSPICE=$NGSPICE"
  done
  mv "$ng/asap7.lib" "$ng/models/asap7.lib"
  stamp "$root" "$id"
}
