"""Reference values for the SKY130 sanity checks.

Source [SKY]: SkyWater SKY130 PDK documentation, "Device Details", sections
"1.8V NMOS FET" and "1.8V PMOS FET"
(https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html),
tables from google/skywater-pdk at 7198cf647113f56041e02abf3eb623692820c5e1:
docs/rules/device-details/nfet_01v8/nfet_01v8-table0.rst and
docs/rules/device-details/pfet_01v8/pfet_01v8-table0.rst.

Each row gives model values per corner and an e-test (EDR) NOM / MIN / MAX.
We check against the EDR MIN-MAX window, because the tables' own TT model
column does not match the released models exactly: our Idsat is about 5 %
(nFET) and 8 % (pFET) above it, and nfet VTXNS15's TT model value (0.645 V)
sits below its own EDR minimum (0.661 V). The deviation from the TT column
is printed for information. The tables do not state the extraction method
for VTX. We use the linear-extrapolation (max-gm) threshold at |Vds| = 50 mV
minus Vds/2: it puts 7 of the 8 Vt rows inside their EDR windows, more than
any constant-current criterion we tried (at most 6). Vt is therefore a
window check, not a value match, and the one row outside is listed in
KNOWN_DEVIATIONS below.

Conditions: TT, 27 C, VDD = 1.8 V, W/L in um as printed.
Ioff (ILK rows) is printed as "Max = <log10 A>" in the TT column; the other
columns of those rows are misaligned in the source table, so only the TT
maximum is used, as an upper bound, with Ioff measured at the source
terminal at Vgs = 0, |Vds| = VDD (the drain current at that bias is
dominated by the simulator's gmin floor).
"""

TEMP = 27
VDD = 1.8

# name: device, W, L, quantity, EDR min, EDR max, TT model value
#   quantity: vt (V, magnitude), idsat (A), ilk (log10 A, upper bound only)
ROWS = [
    ("VTXNL",     "nfet_01v8", 7.00, 8.00, "vt",    0.515,  0.567,  0.538),
    ("VTXNN42",   "nfet_01v8", 0.42, 1.00, "vt",    0.510,  0.590,  0.550),
    ("VTXNS15",   "nfet_01v8", 7.00, 0.15, "vt",    0.661,  0.739,  0.645),
    ("VTSNSN15",  "nfet_01v8", 0.42, 0.15, "vt",    0.625,  0.852,  0.738),
    ("IDSNS15",   "nfet_01v8", 7.00, 0.15, "idsat", 3.039e-3, 3.981e-3, 3.512e-3),
    ("ILKN15",    "nfet_01v8", 7.00, 0.15, "ilk",   None,   -10.25, None),
    ("VTXPLS",    "pfet_01v8", 7.00, 8.00, "vt",    1.014,  1.086,  1.050),
    ("VTXPN42S",  "pfet_01v8", 0.42, 8.00, "vt",    0.895,  0.985,  0.941),
    ("VTXPS15S",  "pfet_01v8", 7.00, 0.15, "vt",    0.705,  0.858,  0.781),
    ("VTXPSN15S", "pfet_01v8", 0.42, 0.15, "vt",    0.554,  0.856,  0.705),
    ("IDSPS15S",  "pfet_01v8", 7.00, 0.15, "idsat", 0.917e-3, 1.777e-3, 1.347e-3),
    ("ILKP15S",   "pfet_01v8", 7.00, 0.15, "ilk",   None,   -7.58,  None),
]
# pFET values are magnitudes; the source prints them negative.

# Rows where the released models disagree with the published table itself,
# reported on every run but not counted as failures.
KNOWN_DEVIATIONS = {
    "VTXNN42": "narrow 0.42/1 nFET: the released TT model gives about 0.60 V, "
               "above both the table's own TT model value (0.550) and its EDR "
               "max; no single Vt definition puts all eight Vt rows in their windows",
}
