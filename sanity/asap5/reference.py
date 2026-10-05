"""Reference values for the ASAP5 sanity checks.

Source [MEJ22]: V. Vashishtha and L. T. Clark, "ASAP5: A predictive PDK for
the 5 nm node," Microelectronics Journal 126 (2022) 105481,
doi:10.1016/j.mejo.2022.105481. The PDK ships it as
asap5PDK_r0p4/docs/asap5_pdk_mej_paper.pdf. Tables 8 (n-NWFET) and 9
(p-NWFET), p. 14: "TT corner parameter (per fin) at 25 C", VDD 0.7 V,
Lg 16 nm, Leff 14 nm. Section 7.1: one "fin" is a vertical stack of two
nanowires, so a single-fin device is nfin = 2 in BSIM-CMG's cylindrical
geometry (geomod = 3), and l is left at the cards' 14 nm.

Extraction definitions:
  Vtsat: constant current, 50 nA, |Vds| = VDD. Stated in [MEJ22] 7.2
         ("Vt is computed using constant current at 50 nA Ids").
  Ioff:  Vgs = 0, |Vds| = VDD, drain current. Stated in 7.0 ("Vds = VDD,
         Vgs = 0 V"); the paper counts GIDL in Ioff ("GIDL < 40 % Ioff"),
         unlike ASAP7's tables.
  DIBL:  (Vtlin - Vtsat) / (0.7 - 0.05 V), both at 50 nA. Not stated; it
         reproduces seven of the eight printed values within 0.1 mV/V.
  SS:    gate swing across the decade from 5 to 50 nA at |Vds| = VDD. Not
         stated; the best of the definitions we tried, but it reads 0.6 to
         0.9 mV/dec below the printed values for every device, a
         systematic offset we cannot explain from the paper.

Tolerances were set after the first comparison, which matched Idsat and
Vtsat to every printed digit; each says why it is that wide.
"""

TEMP = 25
VDD = 0.7
ICC = 50e-9

# per fin: Idsat (uA), Ioff (pA), Vtsat (V, magnitude), DIBL (mV/V), SS (mV/dec)
DEVICES = {
    "nmos_sram": dict(idsat=34.92, ioff=2.87,    vtsat=0.280, dibl=20.06, ss=66.07),
    "nmos_rvt":  dict(idsat=42.90, ioff=17.43,   vtsat=0.226, dibl=22.11, ss=66.07),
    "nmos_lvt":  dict(idsat=50.55, ioff=139.67,  vtsat=0.166, dibl=26.35, ss=66.02),
    "nmos_slvt": dict(idsat=57.42, ioff=1023.93, vtsat=0.110, dibl=27.69, ss=65.99),
    "pmos_sram": dict(idsat=25.29, ioff=1.80,    vtsat=0.319, dibl=27.93, ss=64.56),
    "pmos_rvt":  dict(idsat=37.18, ioff=17.85,   vtsat=0.219, dibl=27.98, ss=64.60),
    "pmos_lvt":  dict(idsat=43.29, ioff=122.45,  vtsat=0.165, dibl=29.16, ss=64.51),
    "pmos_slvt": dict(idsat=49.06, ioff=945.84,  vtsat=0.109, dibl=29.53, ss=64.49),
}

TOL = dict(
    idsat=0.01,   # relative; matched to all printed digits
    ioff=0.10,    # relative; the SRAM devices sit 2-5 % off
    vtsat=0.005,  # V; printed to 3 decimals
    dibl=1.0,     # mV/V
    ss=1.5,       # mV/dec; covers the systematic 0.6-0.9 offset above
)

# Reported on every run, not counted as failures.
KNOWN_DEVIATIONS = {
    ("nmos_sram", "dibl"): "22.1 vs 20.06 printed, while every other device matches within "
                           "0.1 mV/V; [MEJ22] 7.1.1 says the SRAM models were re-derived from "
                           "an earlier calibration rather than new TCAD",
}

# [MEJ22] 7.1: "NMOS Idsat is 3.58x the Idlin and 3.94x for the PMOS" (RVT,
# TT). The Idlin bias is not stated; printed at |Vds| = 50 mV for information.
IDSAT_OVER_IDLIN = {"nmos_rvt": 3.58, "pmos_rvt": 3.94}
