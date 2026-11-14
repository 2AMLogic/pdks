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
| Where | `sg13_lv_nmos`, `sg13_lv_pmos`, `sg13_hv_nmos`, `sg13_hv_pmos` (subckts at lines 66 and 155 of each `*_mod_mismatch.lib`); all four are exercised. Resistors, MIM and MOS caps, varactors and the HBT have `*_mod_mismatch.lib` files too; not exercised. |
| Model | `delvto = agauss(0, delvto_mm/sqrt(m*l*w*1e12), mm_ok)`, `factuo = agauss(1, factuo_mm/sqrt(m*l*w*1e12), mm_ok)`, `w`, `l` = `agauss(w, dw_mm, mm_ok)`, `agauss(l, dl_mm, mm_ok)` (metres). `delvto_mm`, `factuo_mm`, `dw_mm`, `dl_mm` per device: LV nMOS 3.9 mV µm, 0.5 %µm, 4 nm, 2 nm and HV nMOS 7 mV µm, 0.5 %µm, 3 nm, 3 nm (`*_mismatch.lib` lines 20-23); LV pMOS 2.2 mV µm, 0.33 %µm, 4 nm, 2 nm and HV pMOS 4.5 mV µm, 0.4 %µm, 3 nm, 3 nm (lines 25-28) |
| Examples | `ihp-sg13g2/ngspice/mismatch.sp` and `mismatch_hv.sp` (100 samples of a pair, one process, `setseed` + `reset`) and `noise.sp` and `noise_hv.sp` (`.noise` with per-source spectra). Both templates (`ngspice/ihp/{mismatch,noise}.sp.in`) take a device polarity and serve the pMOS too; the installed examples are the nMOS ones. |
| Noise model | PSP 103 cards in `sg13g2_mos{lv,hv}_parm.lib`: thermal `fnto`, flicker `nfalw`, `nfblw`, `nfclw`, `efo`. LV nMOS (lines 124-126) `fnto` 1.0, 7.616e25, 1.026e9, -5e-8, `efo` 1.0; LV pMOS (405-407) `fnto` **1.85**, 2.209e26, 5.723e8, 5.641e-7, `efo` 1.0; HV nMOS (125-127) `fnto` 1.0, 1.42e25, 5.743e8, -3.015e-8, `efo` 1.0; HV pMOS (408-410) `fnto` 1.0, 1.3e25, 5.289e9, 2e-7, `efo` **1.152**. `fntexcl = 0` in every card. The thermal gamma and Nyquist checks divide by the card's own `fnto`, which both quantities are exactly proportional to (a no-op for the three cards at 1.0). |

## Interconnect

Bootstrap installs, next to the models in `<prefix>/ihp-sg13g2/ngspice/`:

- `interconnect.csv`: per layer (None), one row per quantity with its
  status (`published`, `derived` or `gap`) and one source citation. From
  IHP's process specification and layout rules: minimum width and spacing,
  thickness, sheet resistance and its first-order temperature coefficient,
  area capacitance to the layer above, and per via the width and resistance.
  Pitch is width + spacing, and via height is the inter-layer dielectric
  thickness the via spans (both `derived`). **Capacitance per length
  (isolated and at minimum pitch) is a gap on every metal**: the
  specification prints area capacitance only, with no fringe or lateral
  component, and it is not estimated.
- `interconnect.inc`: the published and derived values as
  `.param ihp_sg13g2_<layer>_<w|s|t|p|h|rsh>` (`m2_w`, `m2_rsh`, `v1_w`, …),
  geometry in metres and `rsh` in ohm/sq.
- `wire.inc`: `wire`, `wire1` … `wire64`, the same N-segment pi ladder as
  ASAP7's, shared by both IHP PDKs:
  `X1 a b wire16 l=100u w={ihp_sg13g2_m2_w} rsh={ihp_sg13g2_m2_rsh} cpl=<F/m>`.
  `w`, `rsh` and `cpl` have no default, so a deck that omits one stops with an
  unknown-parameter error. `cpl` is yours to supply from a source you cite.

Sources, at the pinned commit (SHA-256 of each PDF, which bootstrap does not
fetch):

- Process Specification Rev. 1.2 (2023-12-20), `ihp-sg13g2/libs.doc/doc/SG13G2_os_process_spec.pdf`: `974d505886ee62932a50c52c22fbc290db4a70d8a7ce129c0ca8d7934aee160e`, sections 2.13, 2.14, 2.16, 2.17.
- Layout Rules Rev. 0.4 (2024-12-19), `ihp-sg13g2/libs.doc/doc/SG13G2_os_layout_rules.pdf`: `66125e97386dd88ed058b50f4f8e8814c9633069e4060c2b19459d3e3e6450a2`, sections 5.16-5.20, TM1 and TM2.

Nothing here adapts upstream files, so `ngspice/ADAPTATIONS.md` has no entry;
the table is transcribed from the documents above and carries no upstream
file. The sanity checks (`sanity/ihp_spec.py`) compare every row with the
cited value and check the ladder against the closed-form Elmore delay.
