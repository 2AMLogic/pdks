"""Reference values for the SKY130 sanity checks.

Source [SKY]: SkyWater SKY130 PDK documentation, "Device Details", sections
"1.8V NMOS FET" and "1.8V PMOS FET"
(https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html),
and the 1.8 V LVT/HVT flavours of the same section, tables from
google/skywater-pdk at 7198cf647113f56041e02abf3eb623692820c5e1:
docs/rules/device-details/nfet_01v8/nfet_01v8-table0.rst,
docs/rules/device-details/pfet_01v8/pfet_01v8-table0.rst,
docs/rules/device-details/nfet_01v8_lvt/nfet_01v8_lvt-table0.rst,
docs/rules/device-details/pfet_01v8_lvt/pfet_01v8_lvt-table0.rst and
docs/rules/device-details/pfet_01v8_hvt/pfet_01v8_hvt-table0.rst.

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

The pfet_01v8_lvt table names its threshold rows VTC... (the others use
VTX...) and uses L = 0.35 um; it states no different extraction for VTC, so
the same max-gm definition applies. Two of its cells are evidently source
typos and are used as printed: VTCPN42L's EDR window (-1.042 .. -0.845) lies
entirely outside its own TT/NOM value (-0.630), and VTCPSN35L's EDR NOM is
-8.505 (NOM is not used here).
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
    # nfet_01v8_lvt
    ("VTXNLL",    "nfet_01v8_lvt", 7.00, 8.00, "vt",    0.415,  0.465,  0.434),
    ("VTXNN42L",  "nfet_01v8_lvt", 0.42, 1.00, "vt",    0.440,  0.530,  0.485),
    ("VTXNS15L",  "nfet_01v8_lvt", 7.00, 0.15, "vt",    0.556,  0.666,  0.611),
    ("VTXNSN15L", "nfet_01v8_lvt", 0.42, 0.15, "vt",    0.529,  0.750,  0.640),
    ("IDSNS15L",  "nfet_01v8_lvt", 7.00, 0.15, "idsat", 3.527e-3, 4.489e-3, 4.010e-3),
    ("ILKN15L",   "nfet_01v8_lvt", 7.00, 0.15, "ilk",   None,   -9.53,  None),
    # pfet_01v8_lvt
    ("VTCPLL",    "pfet_01v8_lvt", 7.00, 8.00, "vt",    0.518,  0.785,  0.651),
    ("VTCPN42L",  "pfet_01v8_lvt", 0.42, 8.00, "vt",    0.845,  1.042,  0.630),
    ("VTCPS35L",  "pfet_01v8_lvt", 7.00, 0.35, "vt",    0.384,  0.683,  0.533),
    ("VTCPSN35L", "pfet_01v8_lvt", 0.42, 0.35, "vt",    0.316,  0.693,  0.504),
    ("IDSPS35L",  "pfet_01v8_lvt", 7.00, 0.35, "idsat", 1.00e-3, 1.44e-3, 1.22e-3),
    ("ILKP35L",   "pfet_01v8_lvt", 7.00, 0.35, "ilk",   None,   -5.14,  None),
    # pfet_01v8_hvt
    ("VTXPL",     "pfet_01v8_hvt", 7.00, 8.00, "vt",    1.067,  1.141,  1.107),
    ("VTXPN42",   "pfet_01v8_hvt", 0.42, 8.00, "vt",    0.959,  1.056,  1.013),
    ("VTXPS15",   "pfet_01v8_hvt", 7.00, 0.15, "vt",    0.814,  0.963,  0.888),
    ("VTXPSN15",  "pfet_01v8_hvt", 0.42, 0.15, "vt",    0.678,  0.951,  0.819),
    ("IDSPS15",   "pfet_01v8_hvt", 7.00, 0.15, "idsat", 0.697e-3, 1.309e-3, 1.003e-3),
    ("ILKP15",    "pfet_01v8_hvt", 7.00, 0.15, "ilk",   None,   -10.7,  None),
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
    "VTCPN42L": "narrow 0.42/8 LVT pFET: the table's EDR window (0.845 .. 1.042 V) "
                "lies entirely outside its own TT/NOM value (0.630 V), so it looks "
                "like a source typo; the released TT model gives 0.714 V, closer to "
                "the table's TT value than to the window",
    # The table's FS and SF columns contradict each other: for the nFET its
    # Idsat row makes FS the slow corner but its Vt row makes FS fast, and
    # for the pFET the reverse. The models agree with the nFET Idsat row and
    # the pFET Vt row, so the other two rows' FS/SF entries are reported here.
    ("VTXNS15", "fs"): "table's FS/SF Vt columns contradict its own Idsat row; with FS/SF swapped it matches (+0.044); skywater-pdk#450",
    ("VTXNS15", "sf"): "table's FS/SF Vt columns contradict its own Idsat row; with FS/SF swapped it matches (-0.042); skywater-pdk#450",
    ("IDSPS15S", "fs"): "table's FS/SF Idsat columns contradict its own Vt row; with FS/SF swapped it matches (1.319); skywater-pdk#450",
    ("IDSPS15S", "sf"): "table's FS/SF Idsat columns contradict its own Vt row; with FS/SF swapped it matches (0.681); skywater-pdk#450",
}


# ---------------------------------------------------------------------------
# Mismatch (Monte Carlo) and noise. Added for issue #35.
#
# What SkyWater publishes. Searched at the commit above: all 125 .rst files
# under docs/ of google/skywater-pdk 7198cf64 (the "Device Details" tables
# included) contain no Pelgrom coefficient (AVT, ABeta), no mismatch figure,
# no flicker-noise level and no thermal-noise gamma ("mismatch", "pelgrom",
# "flicker" and "noise" appear only in unrelated rows of the layer-key,
# periphery-rule and glossary pages). So there is NO published reference for
# any quantity below; every check is derived from the model files or from
# physics, and the gaps are listed in GAPS.
#
# Mismatch model (pinned tree, sky130_fd_pr 403964dc as built into open_pdks
# f6eeac7). The library corners tt_mm, ff_mm, ... (sky130.lib.spice, e.g.
# `.lib tt_mm` at line 343) set `.param mc_mm_switch=1`; the plain corners set
# it to 0. In sky130_fd_pr__nfet_01v8__tt.pm3.spice every bin has
#   toxe = 4.148e-09 + MC_MM_SWITCH*AGAUSS(0,1,1)*(4.148e-09*toxe_slope/sqrt(l*w*mult))   (line 62)
#   vth0 = 0.5190093 + MC_MM_SWITCH*AGAUSS(0,1,1)*(vth0_slope/sqrt(l*w*mult))              (line 76)
#   voff = -0.1052686 + MC_MM_SWITCH*AGAUSS(0,1,1)*(voff_slope/sqrt(l*w*mult))             (line 102)
# with l, w in um and the slopes in sky130_fd_pr__nfet_01v8__mismatch.corner.spice:
# toxe_slope 3.443e-3 (relative, um), vth0_slope 3.356e-3 (V um), voff_slope
# 0.007 (V um). Each instance draws its own three Gaussians, independent of
# each other. The `.lib mc` corner (mc_pr_switch=1) is process variation, not
# mismatch, and is not used here.
# Devices carrying the switch (a `<dev>__mismatch.corner.spice` file included
# by corners/tt.spice): nfet_01v8, nfet_01v8_lvt, pfet_01v8, pfet_01v8_lvt,
# pfet_01v8_hvt, nfet_03v3_nvt, nfet_05v0_nvt, nfet_g5v0d10v5,
# pfet_g5v0d10v5. Not covered here: resistors, capacitors, BJTs.
VTH0_SLOPE = 3.356e-3   # V um, nfet_01v8__mismatch.corner.spice line 20
TOXE_SLOPE = 3.443e-3   # relative, um, same file line 16
MISMATCH_AREAS = [(1.0, 0.5, 1, 11), (1.0, 0.5, 4, 12), (1.0, 0.5, 16, 13)]   # (W, L um, mult, seed)
# Area is scaled with mult at fixed W/L: the model divides every mismatch term
# by sqrt(l*w*mult) and uses mult nowhere else (the device line,
# nfet_01v8__tt.pm3.spice line 38, has no m=), so the nominal device, its bias
# and its model bin are the same at every area. Scaling
# W and L instead changes bin, and with it the nominal parameters that turn
# the model's vth0/toxe spreads into the extracted Vt and beta spreads, so
# the extracted sigma*sqrt(WL) is not constant across bins (seen: 4/2 um
# gives AVT(Vt) 6.6 against 4.7 mV um at 1/0.5).
MISMATCH_N = 100        # pairs per area; 2N single devices
# Bias: Id = 20 uA * W/L per device (the same at every area); single-device extraction at Vds = 50 mV.
# Extraction definitions (the same ones the deck prints):
#   sigma(dVgs): std of Vgs1 - Vgs2 of two diode-connected devices at equal
#     current, the input-referred offset of a pair at equal drain currents.
#   Vt: linear-extrapolation threshold at the peak of gm = dId/dVg,
#     Vgs - Id/gm - Vds/2, the same definition as the Vt rows above (the
#     deck uses a 10 mV gate grid and the derivative ngspice interpolates).
#   beta = gm,peak / Vds; sigma(beta)/beta = std(gm,peak)/mean(gm,peak).
# Sampling error of a standard deviation from n samples: 1/sqrt(2(n-1)). The
# area-invariance checks (sigma * sqrt(WL) equal at every area, which is the
# Pelgrom area scaling) allow 3 such errors on the deviation of one area from
# the mean of the three.
# sigma(Vt) floor: Vt moves with vth0 one-for-one, and toxe and voff add
# independent variance, so sigma(Vt)*sqrt(WL) cannot be below VTH0_SLOPE
# (a bound, with the same 3-error allowance).
def mc_tol(n):
    return 3.0 / (2.0 * (n - 1)) ** 0.5

# Thermal and flicker noise (nFET 7/8 um at Vg 1.2 V, Vd 0.9 V, saturation,
# Id 44 uA; ngspice .noise, 27 C). The model is BSIM4 with fnoimod=1 and
# tnoimod=1 (lines 57-58 of nfet_01v8__tt.pm3.spice): flicker from
# noia = 2.5e42, noib = noic = 0, em = 4.1e7, ef = 0.84 (lines 211-215);
# thermal from ntnoi = 1.0, tnoia = 1.5e7, tnoib = 9.9e6, rnoia = 0.94,
# rnoib = 0.26 (lines 216-223). These are identical in all 180 bins.
EF = 0.84
FLICKER_SLOPE_TOL = 0.01      # the term is exactly f^-ef; allowance is numerical
# Thermal noise as 4kT*gamma*gm. Long-channel theory (van der Ziel; Tsividis,
# "Operation and Modeling of the MOS Transistor"): gamma = 2/3 in strong
# inversion saturation, rising to 1 as Vds -> 0. A long-channel device
# (7/8 um) is expected inside that range.
GAMMA_LONG = (2.0 / 3.0, 1.0)
# Nyquist: a conductor in equilibrium has channel noise current 4kT*gds. With
# the drain at 0 V the ratio S_id / (4kT*gds0) is exactly 1; 2 % allows for
# the 1 mV finite-difference gds0.
NYQUIST = (0.98, 1.02)
NOISE_BIAS = dict(W=7, L=8, VG=1.2, VD=0.9)
NOISE_BIAS_SHORT = dict(W=7, L=0.15, VG=1.2, VD=0.9)   # information only

# Noise-parameter scan of every *.pm3.spice in the extracted sky130_fd_pr
# (corner variants ff/fs/sf/ss/leak/tt_leak excluded; they repeat the
# parameter set): 50 files, 1308 MOS models. None has noia = 0. Models
# lacking a parameter that the nFET/pFET bins carry (so the model falls back
# to the BSIM4 default for it):
NOISE_SCAN_FILES = 50
NOISE_SCAN_MODELS = 1308
NOISE_ABSENT = {
    "sky130_fd_pr__nfet_g5v0d16v0.pm3.spice": (5, ("ntnoi",)),
    "sky130_fd_pr__pfet_g5v0d16v0.pm3.spice": (2, ("ntnoi", "tnoia")),
    "sky130_fd_pr__special_nfet_latch.pm3.spice": (1, ("ntnoi", "tnoia")),
    "sky130_fd_pr__special_nfet_pass.pm3.spice": (1, ("ntnoi", "tnoia")),
    "sky130_fd_pr__special_nfet_pass_flash.pm3.spice": (2, ("ntnoi", "tnoia")),
    "sky130_fd_pr__special_nfet_pass_lvt.pm3.spice": (1, ("ntnoi",)),
    "sky130_fd_pr__special_pfet_latch.pm3.spice": (2, ("ntnoi", "tnoia", "noia (1 of the 2)")),
}
NOISE_ABSENT_MODELS = 14
# kf is 0 in every model that has it, noib and noic are 0 in most; with
# fnoimod=1 these are not what sets the flicker level (nFET flicker is
# nonzero with kf = 0).

# Known deviations of the noise model from the references above.
NOISE_KNOWN = {
    "gamma": "the released nfet_01v8 gives gamma about 2.05 at 7/8 um (1.21 at 7/0.15), "
             "2 to 3 times the long-channel 2/3 .. 1; the excess is in the model's "
             "thermal noise term itself (channel .id source of the BSIM4 holistic "
             "model, tnoimod=1), not traced to a single parameter",
    "nyquist": "the model's channel thermal noise at Vds = 0 is about 9 % below "
               "4kT*gds0 (0.913); not traced",
}

# Quantities for which no value could be found or derived; listed, not estimated.
GAPS = [
    "Pelgrom coefficients AVT, ABeta: SkyWater publishes none (only the model's own slopes, used above as a floor and as information)",
    "flicker-noise level of the 1.8 V nFET: no published value; the model's level is printed as information only",
    "published thermal-noise gamma: none; only the long-channel theory range is used",
    "mismatch of resistors, capacitors and BJTs; mismatch and noise of the other devices (checked here: nfet_01v8 only)",
    "noise of the models in NOISE_ABSENT: parameters absent, BSIM4 defaults apply",
]
