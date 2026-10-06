# IHP SG13G2 setup, sourced by bootstrap.sh (which provides the helpers).
# shellcheck shell=bash

# shellcheck source=pdks/ihp-sg13g2/upstream.lock
. "$REPO/pdks/ihp-sg13g2/upstream.lock"
# shellcheck source=pdks/ihp-common.sh
. "$REPO/pdks/ihp-common.sh"
# shellcheck disable=SC2034  # read by bootstrap.sh
NEED_OPENVAF=1
GUARD_DIRS+=("$PREFIX/ihp-sg13g2")

setup_ihp_sg13g2() {
  local root="$PREFIX/ihp-sg13g2" src="$PREFIX/ihp-sg13g2/IHP-Open-PDK"
  local id; id="ihp-sg13g2 $IHP_SG13G2_COMMIT openvaf-r $OPENVAF_VERSION $(files_id "$REPO/pdks/ihp-sg13g2/setup.sh" "$REPO/pdks/ihp-common.sh" "$REPO/pdks/ihp-sg13g2/meas.sha256" "$REPO"/ngspice/ihp/*.in)"
  if stamp_ok "$root" "$id"; then
    log "IHP SG13G2: already set up"
    return
  fi
  log "IHP SG13G2: fetching IHP-Open-PDK $IHP_SG13G2_COMMIT (ngspice models and Verilog-A only)"
  claim_dir "$root"
  git_pinned "$IHP_SG13G2_URL" "$IHP_SG13G2_COMMIT" "$src" \
    /LICENSE /ihp-sg13g2/libs.tech/ngspice/ /ihp-sg13g2/libs.tech/verilog-a/
  log "IHP SG13G2: compiling PSP103, R3_CMC and MOSVAR to OSDI"
  ihp_osdi "$src/ihp-sg13g2/libs.tech/verilog-a" "$root/ngspice/osdi" psp103 psp103_nqs r3_cmc mosvar
  ihp_glue ihp-sg13g2 "$src/ihp-sg13g2/libs.tech/ngspice/models" "$root/ngspice/osdi" \
    psp103 psp103_nqs r3_cmc mosvar
  log "IHP SG13G2: fetching measured MOS data (four temperatures)"
  local f sum
  while read -r sum f; do
    fetch "$IHP_SG13G2_RAW/$f" "$sum" "$src/$f"
  done < "$REPO/pdks/ihp-sg13g2/meas.sha256"
  stamp "$root" "$id"
}
