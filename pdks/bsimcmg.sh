# BSIM-CMG 107 Verilog-A -> .osdi, shared by the ASAP7 and ASAP5 setups
# (both PDKs' cards are BSIM-CMG 107). Sourced by them; helpers come from
# bootstrap.sh. Builds once into tools/bsimcmg107.
# shellcheck shell=bash

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

