"""Reference values for the GF180MCU sanity checks.

Sources (both from google/gf180mcu-pdk at de3240d7529a6970437ac3344820aaae7839f215,
published at gf180mcu-pdk.readthedocs.io):

[MRG]  "Model vs. EP Nominal Target", Spice Model Reference Guide section 2.5,
       docs/analog/model_parameters/LV/tables_clear/19_mos_3p3.csv and
       21_mos_6p0.csv. EP specification targets for the slow / typical / fast
       models: Idsat at |Vds| = |Vgs| = VDD, Vbs = 0, and Vth0 by the max-gm
       method (Vds = 0.05 V; 0.1 V for the native device).
[EPS]  "Electrical Parameters Specification", sections 1.0 (3.3 V) and 2.0
       (6 V): docs/analog/spice/elec_specs/tables_clear/1_Low_Voltage_Devices.csv
       and 2_Medium_Voltage_Devices6v.csv. Ioff at |Vds| = 1.1 * VDD, 25 C,
       and subthreshold slope, with min/typ/max limits.

Conditions: 25 C (the temperature [EPS] states), W = 10 um. [MRG] gives
targets for the slow, typical and fast models; they are checked at the
model library's ss, typical and ff corners.

Extraction definitions:
  Vth0: [MRG] says only "max Gm". Taking the tangent at peak gm, its Vgs
        intercept, minus Vds/2 (the usual linear-extrapolation convention)
        reproduces all five typical values to the printed 10 mV; without the
        Vds/2 term every device is off by Vds/2. Inferred, not stated.
  SS:   steepest swing over a 60 mV gate window in subthreshold, at
        |Vds| = 0.05 V. [EPS] gives only an upper limit, so any reasonable
        definition serves.
"""

TEMP = 25

# device: W, L (um), VDD, Vds for Vth0, Idsat typ (uA/um), Vth0 typ (V),
# Ioff limit (pA/um, None = not specified), Vds for Ioff
DEVICES = {
    "nfet_03v3":     dict(w=10, l=0.28, vdd=3.3, vlin=0.05, idsat=510, vth0=0.63, ioff_max=100, voff=3.63),
    "pfet_03v3":     dict(w=10, l=0.28, vdd=3.3, vlin=0.05, idsat=250, vth0=0.73, ioff_max=20, voff=3.63),
    "nfet_06v0":     dict(w=10, l=0.70, vdd=6.0, vlin=0.05, idsat=570, vth0=0.73, ioff_max=10, voff=6.6),
    "pfet_06v0":     dict(w=10, l=0.55, vdd=6.0, vlin=0.05, idsat=290, vth0=0.85, ioff_max=10, voff=6.6),
    "nfet_06v0_nvt": dict(w=10, l=1.80, vdd=6.0, vlin=0.10, idsat=535, vth0=-0.12, ioff_max=None, voff=6.6),
}
# Magnitudes: pFET Idsat and Vth0 are negative in the tables.

# [MRG] slow and fast EP targets: corner -> device -> (Idsat uA/um, Vth0 V)
CORNERS = {
    "ss": {"nfet_03v3": (430, 0.73), "pfet_03v3": (210, 0.85), "nfet_06v0": (480, 0.85),
           "pfet_06v0": (240, 0.98), "nfet_06v0_nvt": (430, 0.08)},
    "ff": {"nfet_03v3": (590, 0.53), "pfet_03v3": (290, 0.61), "nfet_06v0": (660, 0.61),
           "pfet_06v0": (340, 0.72), "nfet_06v0_nvt": (640, -0.32)},
}

SS_MAX = 150.0  # mV/dec, [EPS] max for the four 3.3 V and 6 V devices

# Passives and temperature, [EPS] sections 5.7 (metal TC, from
# 5_General_Specification7.csv), 6.1A/B (high-resistance poly, from
# 6_Passive_Elements1/2.csv) and 6.2 (MIM, 6_Passive_Elements4/5/6.csv).
# [EPS] gives TCs as MIN/TYP/MAX with no temperature range or fit stated.
# We take TC1 as the linear coefficient of a quadratic fit of X(T) about
# 25 C over -40 to 125 C, the range the models were extracted over
# (Spice Model Reference Guide 2.1), and check it within [EPS]'s window.
# Rsheet: R * W / L of a W = 10 um, L = 200 um resistor at 25 C ([EPS]
# monitors film Rs at W = 10 um). C: per area of a 350 x 50 um capacitor at
# V = 0 ([EPS]'s structure). Contact and via TCs are not checked: they have
# no standalone model device.
TEMPS = (-40, -15, 10, 25, 60, 95, 125)
# (model, kind, instance geometry, Rsheet or C/area window, TC1 window ppm/K)
PASSIVES = [
    ("ppolyf_u_1k", "res", "r_width=10u r_length=200u", (800, 1000, 1200), (-1200, -1000, -800)),
    ("ppolyf_u_2k", "res", "r_width=10u r_length=200u", (1600, 2000, 2400), (-1900, -1650, -1300)),
    ("rm1", "metal", "r_width=1u r_length=2000u", None, (2800, 3300, 3800)),
    ("rm2", "metal", "r_width=1u r_length=2000u", None, (2800, 3300, 3800)),
    ("rm3", "metal", "r_width=1u r_length=2000u", None, (2800, 3300, 3800)),
    ("rm4", "metal", "r_width=1u r_length=2000u", None, (2800, 3300, 3800)),
    ("tm6k", "metal", "r_width=2u r_length=2000u", None, (3000, 3500, 4000)),
    ("tm9k", "metal", "r_width=2u r_length=2000u", None, (3100, 3700, 4300)),
    ("tm11k", "metal", "r_width=2u r_length=2000u", None, (3100, 3700, 4300)),
    ("tm30k", "metal", "r_width=2u r_length=2000u", None, (3300, 3900, 4500)),
    ("cap_mim_1f5fF", "cap", "c_width=350u c_length=50u", (1.27, 1.5, 1.73), (9.9, 13.3, 16.6)),
    ("cap_mim_1f0fF", "cap", "c_width=350u c_length=50u", (0.9, 1.0, 1.1), (None, 10, 20)),
    ("cap_mim_2f0fF", "cap", "c_width=350u c_length=50u", (1.8, 2.0, 2.2), (None, 18.8, None)),
]
KNOWN_DEVIATIONS = {
    ("cap_mim_1f5fF", "tc1"): "the model sets c_tc1 = 40.6 ppm/K, outside GF's own 9.9-16.6 ppm/K "
                              "window for the 1.5 fF/um2 MIM (reported: gf180mcu_fd_pr#46; per the "
                              "maintainer, no open-PDK run has used this option, all used 2.0 fF/um2)",
}

TOL = dict(
    idsat=0.02,  # relative; printed to 3 significant figures
    vth0=0.010,  # V; printed to 2 decimals (+-5 mV) plus 5 mV margin
)

# ---------------------------------------------------------------------------
# Interconnect (pdks/gf180mcu/interconnect.csv, installed as
# <prefix>/gf180mcu/ngspice/interconnect.csv)
#
# Sources, all from google/gf180mcu-pdk at de3240d7529a6970437ac3344820aaae7839f215
# (docs published at gf180mcu-pdk.readthedocs.io); SHA-256 of each file is in
# pdks/gf180mcu/README.md:
#
# [DRM] docs/physical_verification/design_manual/tables_clear/22_Metaln_58.csv
#       (rules Mn.1 width, Mn.2a space: M1 0.23 um, M2-M5 0.28 um) and
#       23_Vian_59.csv (Vn.1 via size, Vn.2a via space: 0.26 um).
# [EPS] docs/analog/spice/elec_specs/tables_clear/: 5_General_Specification1.csv
#       (metal sheet resistance, MIN/TYP/MAX in mohm/sq), 5_General_Specification2.csv
#       (via resistance, ohm/via) and 5_General_Specification7.csv
#       (temperature coefficient in %/degC).
# [IA]  docs/analog/layout/inter_specs/tables_clear/3_General_conductor.csv
#       (conductor thickness, "for typical cap", the Raphael technology
#       parameters of the interconnect application note) and
#       5_Sheet_Rho_table.csv (the same sheet resistance, 0.090 +/- 0.014).
#
# Definitions: pitch = width + spacing (derived). Metal levels M1-M5 and
# Via1-Via5 only: MetalTop has four thickness options (6, 9, 11, 30 kA) that
# a design picks, so it is not tabulated. The metal thickness is the
# "typical cap" value of [IA], a simulation parameter rather than an EP
# specification limit; the CSV says so. Capacitance per length exists in
# [IA] only as plots (images/2_cross_section_*.png), which are not
# transcribed, so the isolated and minimum-pitch capacitance per length stay
# gaps, as does the via height. Nothing is estimated or fitted.
#
# Layer: (width, spacing) in nm, [DRM].
METALS = {"M1": (230, 230), "M2": (280, 280), "M3": (280, 280), "M4": (280, 280), "M5": (280, 280)}
THICKNESS = 550  # nm, [IA] 3_General_conductor.csv, M1-M5
RSHEET = 0.090   # ohm/sq, [EPS] 5_General_Specification1.csv typ; window below
RSHEET_WINDOW = (0.076, 0.104)  # [EPS] min, max; [IA] prints 0.090 +/- 0.014 (same)
RSHEET_TC = 0.33  # %/degC, [EPS] 5_General_Specification7.csv typ (min 0.28, max 0.38)
VIAS = {"V1": 260, "V2": 260, "V3": 260, "V4": 260, "V5": 260}  # nm, width and spacing, [DRM]
R_VIA = 4.5      # ohm per via, 0.26 x 0.26 um, [EPS] 5_General_Specification2.csv typ (max 15)
GAP_QUANTITIES = ("c_iso_per_um", "c_pitch_per_um")  # per metal
GAP_VIA_QUANTITIES = ("height",)

# Wire-ladder check (derived: it tests our include against the closed form,
# not a published number). The deck drives an ideal step through RS into a
# wire of N pi segments loaded by CL. The simulated value is the first
# moment of the step response, integral of (vin - vout) dt, and the closed
# form is the Elmore delay
#     RS (C + CL) + R (C / 2 + CL),   R = RSH L / W,   C = CPL L.
# RSH and W are the M1 sheet resistance and minimum width from the table
# (published). CPL is a TEST INPUT chosen so the wire dominates; GF180MCU
# publishes no capacitance per length as a table (a gap above).
ELMORE = dict(l="5m", cpl="0.2n", rs="1k", cl="1f", tstop="50n")
ELMORE_L, ELMORE_CPL = 5e-3, 0.2e-9
ELMORE_RS, ELMORE_CL = 1e3, 1e-15
ELMORE_LAYER = "M1"
ELMORE_SEGMENTS = (1, 4, 64)
# Tolerance: trapezoidal integral on a 2 ps step over 50 ns (about 10 time
# constants, a 5 mm wire so that it dominates the 1 ps input edge); 1e-3 leaves margin
# for a different ngspice build (measured error ~1e-5 for the ASAP7 deck).
ELMORE_TOL = 1e-3
