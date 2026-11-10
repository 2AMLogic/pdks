# IHP SG13G2 (pinned upstream)

| | |
|---|---|
| What | IHP SG13G2 130 nm SiGe BiCMOS (HBTs with fT about 350 GHz) |
| Upstream | https://github.com/IHP-GmbH/IHP-Open-PDK |
| Pin | release v0.3.0, commit `5cccb161` (`upstream.lock`). Sparse, blob-filtered fetch of `ihp-sg13g2/libs.tech/{ngspice,verilog-a}` and `LICENSE` only, about 2.5 MB. Plus eight measured-MOS files from `ihp-sg13g2/libs.doc/meas/MOS` (four temperatures, about 0.65 MB), fetched from the same commit and checked against `meas.sha256`. |
| Licence | Apache-2.0: `LICENSE` here, verbatim. The bundled Verilog-A models carry their own terms: PSP 103.6 and JUNCAP 200 (ECL-2.0, in the file headers), R3_CMC (ECL-2.0; `r3_cmc-LICENSE.txt` and `r3_cmc-NOTICE.txt` here, verbatim), MOSVAR (ASU / Si2 terms in its header). |
| Adaptations | none to PDK files. Bootstrap compiles psp103, psp103_nqs, r3_cmc and mosvar to OSDI with IHP's own flags into `ihp-sg13g2/ngspice/osdi/`, and writes a spiceinit that loads them by absolute path (see `ngspice/ADAPTATIONS.md`). The HBTs are VBIC, built into ngspice. |

## Mismatch and noise

Neither IHP specification publishes a MOS matching coefficient or a noise
level, so the checks (`sanity/ihp_spec.py`, shared with SG13CMOS5L) are derived
from the model files, and the gaps are listed there. Files and lines are in
IHP-Open-PDK `ihp-sg13g2/libs.tech/ngspice/models/` (v0.3.0 `5cccb161`).

| | |
|---|---|
| Mismatch switch | `.lib mos_tt_mismatch` (also `_ss`, `_ff`, `_sf`, `_fs`) includes `sg13g2_mos{lv,hv}_mismatch.lib` and `sg13g2_mos{lv,hv}_mod_mismatch.lib`; the instance parameter `mm_ok` (1 draws, 0 switches every term off) is the switch. Plain `mos_tt` has no mismatch. |
| Where | `sg13_lv_nmos`, `sg13_lv_pmos`, `sg13_hv_nmos`, `sg13_hv_pmos` (subckts at lines 66 and 155 of each `*_mod_mismatch.lib`). Resistors, MIM and MOS caps, varactors and the HBT have `*_mod_mismatch.lib` files too; not exercised. |
| Model | `delvto = agauss(0, delvto_mm/sqrt(m*l*w*1e12), mm_ok)`, `factuo = agauss(1, factuo_mm/sqrt(m*l*w*1e12), mm_ok)`, `w`, `l` = `agauss(w, dw_mm, mm_ok)`, `agauss(l, dl_mm, mm_ok)` (metres). LV nMOS: 3.9 mV µm, 0.5 %µm, 4 nm, 2 nm; HV nMOS: 7 mV µm, 0.5 %µm, 3 nm, 3 nm (`*_mismatch.lib` lines 20-23); pMOS in lines 25-28 |
| Examples | `ihp-sg13g2/ngspice/mismatch.sp` and `mismatch_hv.sp` (100 samples of a pair, one process, `setseed` + `reset`) and `noise.sp` and `noise_hv.sp` (`.noise` with per-source spectra) |
| Noise model | PSP 103 cards in `sg13g2_mos{lv,hv}_parm.lib`: thermal `fnto` (1.0 nMOS, 1.85 LV pMOS), flicker `nfalw`, `nfblw`, `nfclw`, `efo` (LV nMOS 7.616e25, 1.026e9, -5e-8, 1.0; HV nMOS 1.42e25, 5.743e8, -3.015e-8, 1.0); `fntexcl = 0` in every card |
