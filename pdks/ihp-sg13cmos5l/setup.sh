# IHP SG13CMOS5L setup, sourced by bootstrap.sh (which provides the helpers).
# shellcheck shell=bash

# shellcheck source=pdks/ihp-sg13cmos5l/upstream.lock
. "$REPO/pdks/ihp-sg13cmos5l/upstream.lock"
# shellcheck source=pdks/ihp-common.sh
. "$REPO/pdks/ihp-common.sh"
# shellcheck disable=SC2034  # read by bootstrap.sh
NEED_OPENVAF=1
GUARD_DIRS+=("$PREFIX/ihp-sg13cmos5l")

setup_ihp_sg13cmos5l() {
  local root="$PREFIX/ihp-sg13cmos5l" base="$PREFIX/ihp-sg13cmos5l/IHP-Open-PDK"
  local pdk="$base/ihp-sg13cmos5l"
  local id; id="ihp-sg13cmos5l $IHP_CMOS5L_COMMIT openvaf-r $OPENVAF_VERSION $(files_id "$REPO/pdks/ihp-common.sh" "$REPO"/ngspice/ihp/*.in)"
  if stamp_ok "$root" "$id"; then
    log "IHP SG13CMOS5L: already set up"
    return
  fi
  log "IHP SG13CMOS5L: fetching IHP-Open-PDK dev $IHP_CMOS5L_COMMIT (ngspice models and Verilog-A only)"
  claim_dir "$root"
  git_pinned "$IHP_CMOS5L_URL" "$IHP_CMOS5L_COMMIT" "$base" /LICENSE \
    /ihp-sg13g2/libs.tech/ngspice/ /ihp-sg13g2/libs.tech/verilog-a/ \
    /ihp-sg13cmos5l/libs.tech/ngspice/ /ihp-sg13cmos5l/libs.tech/verilog-a/
  log "IHP SG13CMOS5L: compiling PSP103, R3_CMC, MOSVAR and the CMOM capacitors to OSDI"
  # psp103, r3_cmc and mosvar resolve through SG13CMOS5L's symlinks into
  # ../ihp-sg13g2; cap_cmomi and cap_cmomf are SG13CMOS5L's own.
  ihp_osdi "$pdk/libs.tech/verilog-a" "$root/ngspice/osdi" \
    psp103 psp103_nqs r3_cmc mosvar cap_cmomi cap_cmomf
  ihp_glue ihp-sg13cmos5l "$pdk/libs.tech/ngspice/models" "$root/ngspice/osdi" \
    psp103 psp103_nqs r3_cmc mosvar cap_cmomi cap_cmomf
  stamp "$root" "$id"
}
