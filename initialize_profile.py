"""
Initialize profile for PDF refinement. This script belongs to the
initialize_profile stage.

This script requires:
    - profile_path variable as the input.
    - optional qmin, qmax, xmin, xmax, and dx variables as inputs.

This script provides:
    - profile: diffpy.srfit.fitbase.Profile
variables as the output.
"""

# imports
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.pdf import PDFParser
from pathlib import Path

# Input parameters
profile_path = Path("data/Ni.gr").resolve()
qmax = None
qmin = None
xmin = None
xmax = None
dx = None

# script body
profile = Profile()
parser = PDFParser()
parser.parseString(Path(profile_path).read_text())
profile.loadParsedData(parser)
if qmin:
    profile.meta["qmin"] = qmin
if qmax:
    profile.meta["qmax"] = qmax
profile.setCalculationRange(xmin=xmin, xmax=xmax, dx=dx)
