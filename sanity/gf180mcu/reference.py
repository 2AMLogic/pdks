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
                              "window for the 1.5 fF/um2 MIM; the 1.0 and 2.0 fF models are 13 and 15",
}

TOL = dict(
    idsat=0.02,  # relative; printed to 3 significant figures
    vth0=0.010,  # V; printed to 2 decimals (+-5 mV) plus 5 mV margin
)
