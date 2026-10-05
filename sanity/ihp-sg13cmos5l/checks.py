"""IHP SG13CMOS5L sanity checks: LV MOS against the SG13CMOS5L process
specification (same rows and definitions as SG13G2's). Sources and
definitions: sanity/ihp_spec.py. Run via sanity/run.py --pdk ihp-sg13cmos5l.
"""

import os

import ihp_spec


def run(prefix, ng):
    models = os.path.join(prefix, "ihp-sg13cmos5l", "IHP-Open-PDK", "ihp-sg13cmos5l", "libs.tech", "ngspice", "models")
    return ihp_spec.run(prefix, "ihp-sg13cmos5l", models, hbt=False)
