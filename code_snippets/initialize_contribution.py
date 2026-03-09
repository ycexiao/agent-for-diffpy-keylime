"""
Initialize a single contribution for PDF refinement. This script belongs to
the initialize_contribution stage

This script requires:
  - profile variable from initialize_profile stage.
  - pdfgenerators variable from initialize_structure stage.
  - optional equation_string variable as the input.

This script provides:
  - contribution: diffpy.srfit.fitbase.FitContribution
variables as the output.
"""

# ===========================
# imports
# ===========================
from diffpy.srfit.fitbase import FitContribution

# ===========================
# input parameters
# ===========================
profile = None
pdfgenerator = None
equation_string = "s0*G1"

# ===========================
# Output parameters
# ===========================
contribution = None

# ===========================
# script body
# ===========================
contribution = FitContribution("pdfcontribution")
contribution.setProfile(profile)
contribution.addProfileGenerator(pdfgenerator)
contribution.setEquation(equation_string)
