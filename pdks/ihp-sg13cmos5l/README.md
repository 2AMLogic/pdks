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
