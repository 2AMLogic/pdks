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

## Mismatch and noise

Neither IHP specification publishes a MOS matching coefficient or a noise
level, so the checks (`sanity/ihp_spec.py`, shared with SG13G2) are derived
from the model files, and the gaps are listed there. Files and lines are in
IHP-Open-PDK `ihp-sg13g2/libs.tech/ngspice/models/` (dev `8e07a1f1`; the MOS files are the ones SG13G2 uses).

| | |
|---|---|
| Mismatch switch | `.lib mos_tt_mismatch` (also `_ss`, `_ff`, `_sf`, `_fs`) includes `sg13g2_mos{lv,hv}_mismatch.lib` and `sg13g2_mos{lv,hv}_mod_mismatch.lib`; the instance parameter `mm_ok` (1 draws, 0 switches every term off) is the switch. Plain `mos_tt` has no mismatch. |
| Where | `sg13_lv_nmos`, `sg13_lv_pmos`, `sg13_hv_nmos`, `sg13_hv_pmos` (subckts at lines 66 and 155 of each `*_mod_mismatch.lib`). Resistors, MIM and MOS caps, varactors and the HBT have `*_mod_mismatch.lib` files too; not exercised. |
| Model | `delvto = agauss(0, delvto_mm/sqrt(m*l*w*1e12), mm_ok)`, `factuo = agauss(1, factuo_mm/sqrt(m*l*w*1e12), mm_ok)`, `w`, `l` = `agauss(w, dw_mm, mm_ok)`, `agauss(l, dl_mm, mm_ok)` (metres). LV nMOS: 3.9 mV µm, 0.5 %µm, 4 nm, 2 nm; HV nMOS: 7 mV µm, 0.5 %µm, 3 nm, 3 nm (`*_mismatch.lib` lines 20-23); pMOS in lines 25-28 |
| Examples | `ihp-sg13cmos5l/ngspice/mismatch.sp` and `mismatch_hv.sp` (100 samples of a pair, one process, `setseed` + `reset`) and `noise.sp` and `noise_hv.sp` (`.noise` with per-source spectra) |
| Noise model | PSP 103 cards in `sg13g2_mos{lv,hv}_parm.lib`: thermal `fnto` (1.0 nMOS, 1.85 LV pMOS), flicker `nfalw`, `nfblw`, `nfclw`, `efo` (LV nMOS 7.616e25, 1.026e9, -5e-8, 1.0; HV nMOS 1.42e25, 5.743e8, -3.015e-8, 1.0); `fntexcl = 0` in every card |
| Difference from SG13G2 | none in values. The default of `mm_ok` in `*_mod_mismatch.lib` is 0 here (1 in SG13G2), so the examples set it explicitly. Its specification has no MOS matching row either. |

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
