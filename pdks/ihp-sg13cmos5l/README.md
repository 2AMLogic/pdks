# IHP SG13CMOS5L (pinned upstream)

| | |
|---|---|
| What | IHP SG13CMOS5L, the 130 nm CMOS-only, 5-metal derivative of SG13G2 |
| Upstream | https://github.com/IHP-GmbH/ihp-sg13cmos5l, inside https://github.com/IHP-GmbH/IHP-Open-PDK |
| Pins | SG13CMOS5L commit `607e18d4` (2026-08-25), and IHP-Open-PDK dev commit `34fd0c72` (the dev tip at that date). SG13CMOS5L's MOS models and Verilog-A are symlinks into an IHP-Open-PDK dev checkout, and its README requires that layout. v0.3.0 lacks files it links to. Both fetches are sparse and blob-filtered, about 5 MB together. |
| Licence | Apache-2.0: `LICENSE` here, verbatim (identical in both repositories). Bundled Verilog-A: PSP 103.8.2 and JUNCAP 200 (NXP Semiconductors, TU Delft and CEA terms in `releasenotesPSP103.8.2.txt`: modify, copy and redistribute; no charge for their code itself; acknowledge them in product documentation; keep the copyright notice, disclaimer and conditions, including with binaries), R3_CMC (ECL-2.0; `r3_cmc-*.txt` here, verbatim), MOSVAR (ASU / Si2 terms), cap_cmomi / cap_cmomf (Apache-2.0). |
| Adaptations | none to PDK files. Bootstrap compiles psp103, psp103_nqs, r3_cmc, mosvar, cap_cmomi and cap_cmomf to OSDI into `ihp-sg13cmos5l/ngspice/osdi/`. The repository's own prebuilt `cap_cmom*.osdi` are Linux x86-64 binaries and are not used. |

Upstream note: IHP archived the ihp-sg13cmos5l repository on 2026-09-23 and
moved its content into IHP-Open-PDK's `dev` branch (`ihp-sg13cmos5l/`). The
pinned commits stay fetchable. Re-pinning to a single IHP-Open-PDK commit
that holds both is the next update for this PDK.
