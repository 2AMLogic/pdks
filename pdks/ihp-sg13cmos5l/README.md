# IHP SG13CMOS5L (pinned upstream)

| | |
|---|---|
| What | IHP SG13CMOS5L, the 130 nm CMOS-only, 5-metal derivative of SG13G2 |
| Upstream | https://github.com/IHP-GmbH/IHP-Open-PDK, `dev` branch, `ihp-sg13cmos5l/` |
| Pin | IHP-Open-PDK dev commit `8e07a1f1` (the dev tip on 2026-10-05). SG13CMOS5L's MOS models and Verilog-A are symlinks into `../ihp-sg13g2`, so both directories are fetched. Release v0.3.0 predates SG13CMOS5L. Sparse, blob-filtered fetch, about 5 MB. |
| Licence | Apache-2.0: `LICENSE` here, verbatim (identical in both repositories). Bundled Verilog-A: PSP 103.8.2 and JUNCAP 200 (NXP Semiconductors, TU Delft and CEA terms in `releasenotesPSP103.8.2.txt`: modify, copy and redistribute; no charge for their code itself; acknowledge them in product documentation; keep the copyright notice, disclaimer and conditions, including with binaries), R3_CMC (ECL-2.0; `r3_cmc-*.txt` here, verbatim), MOSVAR (ASU / Si2 terms), cap_cmomi / cap_cmomf (Apache-2.0). |
| Adaptations | none to PDK files. Bootstrap compiles psp103, psp103_nqs, r3_cmc, mosvar, cap_cmomi and cap_cmomf to OSDI into `ihp-sg13cmos5l/ngspice/osdi/`. The repository's own prebuilt `cap_cmom*.osdi` are Linux x86-64 binaries and are not used. |

History: until 2026-09-23, SG13CMOS5L was a separate repository
(IHP-GmbH/ihp-sg13cmos5l, now archived) meant to be checked out inside
IHP-Open-PDK dev. This repo first pinned that layout (ihp-sg13cmos5l
`607e18d4` inside IHP-Open-PDK `34fd0c72`). Moving to the single dev commit
left every sanity-check value unchanged.

## Interconnect

Bootstrap installs, next to the models in `<prefix>/ihp-sg13cmos5l/ngspice/`:

- `interconnect.csv`: per layer (None), one row per quantity with its
  status (`published`, `derived` or `gap`) and one source citation. From
  IHP's process specification and layout rules: minimum width and spacing,
  thickness, sheet resistance and its first-order temperature coefficient,
  area capacitance to the layer above, and per via the width and resistance.
  Pitch is width + spacing, and via height is the inter-layer dielectric
  thickness the via spans (both `derived`). **Capacitance per length
  (isolated and at minimum pitch) is a gap on every metal**: the
  specification prints area capacitance only, with no fringe or lateral
  component, and it is not estimated. SG13CMOS5L's specification prints two quantities as `tbd` (Metal4 to TopMetal1 area capacitance and TopVia1 resistance); they are gaps too.
- `interconnect.inc`: the published and derived values as
  `.param ihp_sg13cmos5l_<layer>_<w|s|t|p|h|rsh>` (`m2_w`, `m2_rsh`, `v1_w`, …),
  geometry in metres and `rsh` in ohm/sq.
- `wire.inc`: `wire`, `wire1` … `wire64`, the same N-segment pi ladder as
  ASAP7's, shared by both IHP PDKs:
  `X1 a b wire16 l=100u w={ihp_sg13cmos5l_m2_w} rsh={ihp_sg13cmos5l_m2_rsh} cpl=<F/m>`.
  `rsh` and `cpl` have no default, so a deck that omits one stops with an
  unknown-parameter error. `cpl` is yours to supply from a source you cite.

Sources, at the pinned commit (SHA-256 of each PDF, which bootstrap does not
fetch):

- Process Specification Rev. 0.2, `ihp-sg13cmos5l/libs.doc/doc/SG13CMOS5L_os_process_spec.pdf`: `26e28c28024411a98b7f3dd586f2c4c8bba832904e5a75935cebeb3264b378cd`, sections 3.1, 3.4, 3.6, 3.7.
- Layout Rules Rev. 0.1 (2025-12-08), `ihp-sg13cmos5l/libs.doc/doc/SG13CMOS5L_os_layout_rules.pdf`: `6c921a403b30c30950b43664204ee6a567e7a33166a74a0e48cabd2a0c7bbc1d`, sections 5.14-5.18, TV1 and TM1.
- The BEOL values are the same as SG13G2's (SG13CMOS5L stops at Metal4 and TopMetal1); each row's `source` names the SG13CMOS5L section and says so.

Nothing here adapts upstream files, so `ngspice/ADAPTATIONS.md` has no entry;
the table is transcribed from the documents above and carries no upstream
file. The sanity checks (`sanity/ihp_spec.py`) compare every row with the
cited value and check the ladder against the closed-form Elmore delay.
