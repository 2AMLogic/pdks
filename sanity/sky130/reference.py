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

# Corners. The same tables give model values at FF, SS, FS and SF. Because
# their TT column is already off the released models, corners are checked
# relative to TT: Idsat as the ratio corner / TT (within 3 %), Vt as the
# shift corner - TT (within 15 mV), both for the 7/0.15 devices.
# (row, device, quantity, TT, {corner: value}); pFET values are magnitudes.
CORNER_ROWS = [
    ("VTXNS15",  "nfet_01v8", "vt",    0.645,  {"ff": 0.615, "ss": 0.677, "fs": 0.603, "sf": 0.689}),
    ("IDSNS15",  "nfet_01v8", "idsat", 3.512,  {"ff": 3.945, "ss": 3.078, "fs": 3.041, "sf": 3.983}),
    ("VTXPS15S", "pfet_01v8", "vt",    0.781,  {"ff": 0.728, "ss": 0.835, "fs": 0.705, "sf": 0.858}),
    ("IDSPS15S", "pfet_01v8", "idsat", 1.347,  {"ff": 1.742, "ss": 0.952, "fs": 0.917, "sf": 1.777}),
]
CORNER_TOL = dict(idsat=0.03, vt=0.015)

# The tables' TT column matches SkyWater's continuous ("combined") models,
# which ship in the same open_pdks build (libs.tech/combined, added to
# sky130_fd_pr in be6d00ed, 2023), rather than the binned models that
# libs.tech/ngspice loads by default. The default models' Idsat is 5-8 %
# above the TT column; the continuous models' is within 0.5 %. So the TT
# Idsat rows are also checked against the continuous models, within 1 %
# (the column prints 4 significant figures). Vt is not: its extraction
# method is unstated, and neither model set matches the TT Vt column.
COMBINED_IDSAT = [("IDSNS15", "nfet_01v8", 3.512e-3), ("IDSPS15S", "pfet_01v8", 1.347e-3)]
COMBINED_TOL = 0.01

# Rows where the released models disagree with the published table itself,
# reported on every run but not counted as failures.
KNOWN_DEVIATIONS = {
    "VTXNN42": "narrow 0.42/1 nFET: the released TT model gives about 0.60 V, "
               "above both the table's own TT model value (0.550) and its EDR "
               "max; no single Vt definition puts all eight Vt rows in their windows",
    # The table's FS and SF columns contradict each other: for the nFET its
    # Idsat row makes FS the slow corner but its Vt row makes FS fast, and
    # for the pFET the reverse. The models agree with the nFET Idsat row and
    # the pFET Vt row, so the other two rows' FS/SF entries are reported here.
    ("VTXNS15", "fs"): "table's FS/SF Vt columns contradict its own Idsat row; with FS/SF swapped it matches (+0.044); skywater-pdk#450",
    ("VTXNS15", "sf"): "table's FS/SF Vt columns contradict its own Idsat row; with FS/SF swapped it matches (-0.042); skywater-pdk#450",
    ("IDSPS15S", "fs"): "table's FS/SF Idsat columns contradict its own Vt row; with FS/SF swapped it matches (1.319); skywater-pdk#450",
    ("IDSPS15S", "sf"): "table's FS/SF Idsat columns contradict its own Vt row; with FS/SF swapped it matches (0.681); skywater-pdk#450",
}
