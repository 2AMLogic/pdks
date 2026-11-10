"""Reference values for the TR-1um sanity checks.

Source [OS00]: Tokai Rika / OpenSUSI, "TR-1um reference manual" rev. 1.1
(OS00_リファレンスマニュアル_rev1.1.pdf), in OpenSUSI/TR-1um at
c5bcc378 under openIP62/IP62/Technology/doc/. Apache-2.0.

Table I-2-7 (p. 11) plots Id-Vg (|Vds| = 5 V) and Id-Vd (to |Vds| = 7 V)
for the 5 V NMOS and PMOS at W/L = 30/1 um, measured (実測) and simulated
("sim") with Tokai Rika's models. It prints no numbers: the values below
were read off the "sim" curves of the figure's images (pixel digitisation,
about +-2 %; the image crops the y-axis labels, so the scale comes from the
grid). They are compared with a 5 % tolerance: digitisation error plus
margin. Labelled "published (digitised)".

Measured silicon values from the same figure, and Table I-2-3 (p. 8;
VTHO 0.85 / -0.93 V, VTH +-0.55 V, beta0 1.1 / -0.3 mA/V2 at W/L 12.5/1),
are printed for information only: the table states no extraction method,
and the models are fitted to Tokai Rika's simulation, not to the silicon
points. Conditions: typical models (the only public set), 25 C (the
manual's Ta).
"""

TEMP = 25
TOL = 0.05

# (device, curve, |Vgs|, |Vds|, sim (A), measured (A))
POINTS = [
    ("NMOS", "Id-Vg", 2, 5, 1.20e-3, 1.48e-3),
    ("NMOS", "Id-Vg", 3, 5, 3.19e-3, 3.61e-3),
    ("NMOS", "Id-Vg", 4, 5, 5.63e-3, 5.95e-3),
    ("NMOS", "Id-Vg", 5, 5, 8.28e-3, 8.26e-3),
    ("NMOS", "Id-Vd", 2, 7, 1.27e-3, 1.80e-3),
    ("NMOS", "Id-Vd", 3, 7, 3.24e-3, 4.05e-3),
    ("NMOS", "Id-Vd", 4, 7, 5.65e-3, 6.31e-3),
    ("NMOS", "Id-Vd", 5, 7, 8.31e-3, 8.53e-3),
    ("NMOS", "Id-Vd", 6, 7, 11.15e-3, 10.71e-3),
    ("PMOS", "Id-Vg", 2, 5, 0.41e-3, 0.47e-3),
    ("PMOS", "Id-Vg", 3, 5, 1.17e-3, 1.31e-3),
    ("PMOS", "Id-Vg", 4, 5, 2.13e-3, 2.34e-3),
    ("PMOS", "Id-Vg", 5, 5, 3.22e-3, 3.47e-3),
    ("PMOS", "Id-Vd", 3, 7, 1.26e-3, 1.37e-3),
    ("PMOS", "Id-Vd", 4, 7, 2.26e-3, 2.45e-3),
    ("PMOS", "Id-Vd", 5, 7, 3.41e-3, 3.63e-3),
    ("PMOS", "Id-Vd", 6, 7, 4.64e-3, 4.87e-3),
]

# Reported on every run, not counted as failures.
KNOWN_DEVIATIONS = {
    ("PMOS", "Id-Vd", 3): "PMOS runs 1-6 % below the plotted sim curve, most at low overdrive; "
                          "the figure may come from an earlier card version (NMOS matches within 2 %)",
}


# ---------------------------------------------------------------------------
# Mismatch and noise. Added for issue #43.
#
# What Tokai Rika publishes. [OS00] Table I-1-2 "Document list" (p. 6) lists
# "Noise model" and "Matching" (マッチング) among the documents with the entry
# 無 (none): neither exists in the open release. The other manuals (OS02
# circuit-simulation guideline) mention neither. So there is NO published
# mismatch coefficient and NO noise level; both are gaps.
#
# Mismatch: the model cards have no statistical content. The only variation
# hooks are the global parameters vthMN, vthMP, vthMNE, vthMPE (ip62_models,
# set to 0 and added to vth0 of every instance alike: a shift, not a
# spread), and models_IP62_*.lib contain no agauss, gauss, unif or mc_ term.
# So there is no mismatch deck for TR-1um, and no Pelgrom check.
MISMATCH_TOKENS = ("agauss", "gauss", "aunif", "unif", "mc_", "mismatch")
MISMATCH_SCAN_FILES = 4          # models_IP62_{mos,res,cap,diode}.lib

# Noise: the MOS cards (BSIM3v3, level 49: PMOS_mst, NMOS_mst, MPE_mst,
# MNE_mst in models_IP62_mos_v2.lib) set none of noimod, noia, noib, noic,
# em, ef, kf, af, so the BSIM3v3 defaults apply: noimod = 1, kf = 0. The
# flicker term (noimod = 1: kf-scaled) is therefore exactly 0; the thermal
# term is the charge-based channel expression, 2/3 * 4kT * (gm + gmbs + gds).
# The deck (NMOS 30/10 um, Vg = Vd = 2.5 V, ngspice .noise, 27 C) shows that.
NOISE_PARAMS = ("noimod", "noia", "noib", "noic", "em", "ef", "kf", "af")
MOS_MODELS = 4
GAMMA_LONG = (2.0 / 3.0, 1.0)    # long-channel theory, as in sanity/gf180mcu/reference.py
NYQUIST = (0.98, 1.02)
NOISE_BIAS = dict(W=30, L=10, VG=2.5, VD=2.5)
NOISE_BIAS_SHORT = dict(W=30, L=1, VG=2.5, VD=2.5)       # information only
NOISE_KNOWN = {
    "nyquist": "S_id/(4kT*gds) at Vds = 0 is 2/3 (0.667): BSIM3v3 thermal noise is a fixed 2/3 * 4kT*(gm+gmbs+gds) "
               "and does not rise to 4kT*gds in the triode limit",
}
GAPS = [
    "mismatch: no model (Table I-1-2 \"Matching\": none; no statistical parameter in any card); no Pelgrom coefficient",
    "noise: no published model or level (Table I-1-2 \"Noise model\": none); the cards set no noise parameter, so flicker is 0 and thermal is the BSIM3v3 default",
]

# ---------------------------------------------------------------------------
# Interconnect (pdks/tr1um/interconnect.csv, installed as
# <prefix>/tr1um/ngspice/interconnect.csv)
#
# [DR] = Document/TR-1um_Drawing_Layer_DR_Table.csv in OpenSUSI/TR-1um at
# c5bcc378 (SHA-256 in pdks/tr1um/files.sha256, fetched by bootstrap.sh).
# Units are um (GC.W1, the 1.0 minimum gate length, fixes the scale). It is
# the only file at the pin that prints per-layer metal geometry:
#     M1.W1 width min 1.8   M1.S1 space min 1.4   (M1.W2/M1.SW wide metal
#     M2.W1 width min 3.0   M2.S1 space min 2.0    rules are not used)
#     V1.W1 width fixed 1.4
# Pitch is width + spacing, a derived value. The reference manual [OS00]
# (and the circuit-simulation guideline OS02 at the same path) was searched
# for sheet resistance, capacitance, thickness and via resistance: its
# tables I-2-4 and I-2-5 print sheet resistance and capacitance for the
# diffusion and poly-Si resistors and the CSIO capacitor only, table I-3-1
# prints electromigration current limits (M1 2 um 900 uA, M2 3 um 3.7 mA),
# and the process cross-section figures are marked 非公開 (not disclosed).
# Nothing there is a metal sheet resistance, a wire capacitance or a via
# resistance, so those are explicit gaps in the table. The resistor/capacitor
# calculator workbook (抵抗・容量計算ツール) is for devices and is not
# fetched. Poly-Si (RS, 120 ohm/sq) is a resistor layer, not a wire in this
# table.
#
# Rule name -> MIN column of [DR] (um); checked against the fetched file.
DR_RULES = {"M1.W1": 1.8, "M1.S1": 1.4, "M2.W1": 3.0, "M2.S1": 2.0, "V1.W1": 1.4}
# Metal layer: (width, spacing) in um, [DR].
METALS = {"M1": (DR_RULES["M1.W1"], DR_RULES["M1.S1"]), "M2": (DR_RULES["M2.W1"], DR_RULES["M2.S1"])}
VIAS = {"V1": DR_RULES["V1.W1"]}  # width in um, [DR] V1.W1 (fixed)
GAP_QUANTITIES = ("thickness", "rsheet", "rsheet_tcr", "c_iso_per_um", "c_pitch_per_um")  # per metal
GAP_VIA_QUANTITIES = ("height", "r_via")

# Wire-ladder check (derived: it tests our include against the closed form,
# not a published number). The deck drives an ideal step through RS into a
# wire of N pi segments loaded by CL. The simulated value is the first
# moment of the step response, integral of (vin - vout) dt, and the closed
# form is the Elmore delay
#     RS (C + CL) + R (C / 2 + CL),   R = RSH L / W,   C = CPL L.
# For a pi ladder this holds for every N (the distributed line's R C / 2).
# RSH and CPL below are TEST INPUTS chosen so the wire dominates; they are
# not TR-1um values (TR-1um publishes none, see above). W is the M1 width.
ELMORE = dict(l="20u", w="1.8u", rsh=5000.0, cpl="0.2n", rs="1k", cl="1f", tstop="10n")
ELMORE_L, ELMORE_W, ELMORE_RSH, ELMORE_CPL = 20e-6, 1.8e-6, 5000.0, 0.2e-9
ELMORE_RS, ELMORE_CL = 1e3, 1e-15
ELMORE_SEGMENTS = (1, 4, 64)
# Tolerance: same time scale as the ASAP7 check (R 55.6 kohm, C 4 fF), so
# its measured trapezoid error (~1e-5) applies; 1e-3 leaves margin.
ELMORE_TOL = 1e-3
