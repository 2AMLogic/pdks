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

TOL = dict(
    idsat=0.02,  # relative; printed to 3 significant figures
    vth0=0.010,  # V; printed to 2 decimals (+-5 mV) plus 5 mV margin
)
