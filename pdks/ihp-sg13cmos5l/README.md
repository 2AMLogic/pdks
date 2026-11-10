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
