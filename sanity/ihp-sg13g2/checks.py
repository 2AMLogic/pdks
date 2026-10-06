"""IHP SG13G2 sanity checks: LV MOS and npn13G2 HBT against the SG13G2
process specification. Sources and definitions: sanity/ihp_spec.py.
Run via sanity/run.py --pdk ihp-sg13g2.
"""

import os

import ihp_spec


def run(prefix, ng):
    models = os.path.join(prefix, "ihp-sg13g2", "IHP-Open-PDK", "ihp-sg13g2", "libs.tech", "ngspice", "models")
    src = os.path.join(prefix, "ihp-sg13g2", "IHP-Open-PDK")
    return ihp_spec.run(prefix, "ihp-sg13g2", models, hbt=True, meas_src=src)
