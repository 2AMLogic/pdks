# Tokai Rika TR-1um (pinned upstream)

| | |
|---|---|
| What | Tokai Rika 1 µm CMOS (OpenSUSI's IP62 open release): 5 V NMOS and PMOS, plus diodes, resistors and capacitors |
| Upstream | https://github.com/OpenSUSI/TR-1um |
| Pin | release v1.2609.0, commit `c5bcc378` (`upstream.lock`). The six files under `libs.tech/spice/models/` and `LICENSE` are fetched one by one and checked against `files.sha256` (about 30 KB). |
| Licence | Apache-2.0. `LICENSE` (OpenSUSI, ISHI-KAI, Tokai Rika) and `IP62-LICENSE.txt` (Tokai Rika's notice for the original IP62 data) are upstream's, verbatim. No NOTICE file. |
| Adaptations | none for the MOSFETs. They are BSIM3v3 subcircuits and load in ngspice unchanged, including the `simulator lang=spectre` comment line. |

Caveats:
- **Typical corner only.** Tokai Rika marks its corner model sets
  "非公開" (not disclosed).
- **Weak reference data.** The only device reference data are plotted
  curves (reference manual, Table I-2-7), which we digitised, so the
  checks are coarse (±5 %).
- **Capacitor CSIO doesn't load.** ngspice can't parse its
  voltage-dependent capacitor with `m=m` ("unknown parameter (e9)").
  Instantiating CSIO fails; the other models load fine.
- **RR resistor unchecked.** It reads about 36 % below its table value
  for a reason we haven't identified, so it isn't checked.
