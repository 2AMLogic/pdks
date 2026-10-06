# IHP SG13G2 (pinned upstream)

| | |
|---|---|
| What | IHP SG13G2 130 nm SiGe BiCMOS (HBTs with fT about 350 GHz) |
| Upstream | https://github.com/IHP-GmbH/IHP-Open-PDK |
| Pin | release v0.3.0, commit `5cccb161` (`upstream.lock`). Sparse, blob-filtered fetch of `ihp-sg13g2/libs.tech/{ngspice,verilog-a}` and `LICENSE` only, about 2.5 MB. Plus eight measured-MOS files from `ihp-sg13g2/libs.doc/meas/MOS` (four temperatures, about 0.65 MB), fetched from the same commit and checked against `meas.sha256`. |
| Licence | Apache-2.0: `LICENSE` here, verbatim. The bundled Verilog-A models carry their own terms: PSP 103.6 and JUNCAP 200 (ECL-2.0, in the file headers), R3_CMC (ECL-2.0; `r3_cmc-LICENSE.txt` and `r3_cmc-NOTICE.txt` here, verbatim), MOSVAR (ASU / Si2 terms in its header). |
| Adaptations | none to PDK files. Bootstrap compiles psp103, psp103_nqs, r3_cmc and mosvar to OSDI with IHP's own flags into `ihp-sg13g2/ngspice/osdi/`, and writes a spiceinit that loads them by absolute path (see `ngspice/ADAPTATIONS.md`). The HBTs are VBIC, built into ngspice. |
