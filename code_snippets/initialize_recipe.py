"""
Initialize recipe for single phase PDF refinement. This script belongs to the
initialize_recipe stage.

This script requires:
  - contribution: diffpy.srfit.fitbase.FitContribution from initialize_contribution stage.
  - pdfgenerators: List[diffpy.srfit.pdf.PDFGenerator] from initialize_structure stage.
  - spacegroups: List[str] from initialize_structure stage.
  - optional parameter_values_dictionary variable as the input for setting initial parameter values.

This script provides:
  - recipe: diffpy.srfit.fitbase.FitRecipe
variables as the output.
"""

# ===========================
# imports
# ===========================
from diffpy.srfit.fitbase import FitRecipe
from diffpy.srfit.fitbase.constrainer import constrainAsSpaceGroup
import warnings

# ===========================
# input parameters
# ===========================
contribution = None
pdfgenerator = None
spacegroup = None
parameter_values_dictionary = {}

# ===========================
# output parameters
# ===========================
recipe = None

# ===========================
# script body
# ===========================
recipe = FitRecipe()
recipe.addContribution(contribution)
delta1 = getattr(pdfgenerator, "delta1")
delta2 = getattr(pdfgenerator, "delta2")
s0 = getattr(contribution, "s0")
qdamp = getattr(pdfgenerator, "qdamp")
qbroad = getattr(pdfgenerator, "qbroad")
recipe.addVar(delta1, name="delta1", fixed=False)
recipe.addVar(delta2, name="delta2", fixed=False)
recipe.addVar(s0, name="s0", fixed=False)
recipe.addVar(qdamp, name="qdamp", fixed=False)
recipe.addVar(qbroad, name="qbroad", fixed=False)
structure_parset = pdfgenerator.phase
spacegroupparams = constrainAsSpaceGroup(structure_parset, spacegroup)
for par in spacegroupparams.latpars:
    recipe.addVar(par, name=par.name, fixed=False)
for par in spacegroupparams.xyzpars:
    recipe.addVar(par, name=par.name, fixed=False)
for par in spacegroupparams.adppars:
    recipe.addVar(par, name=par.name, fixed=False)
recipe.fix("all")
for parameter_name, parameter_value in parameter_values_dictionary.items():
    parameter_obj = recipe._parameters.get(parameter_name, None)
    if parameter_obj is not None:
        parameter_obj.setValue(parameter_value)
    else:
        warnings.warn(
            f"Parameter {parameter_name} not found in the recipe. "
            "Skipping setting its initial value."
        )
# 0 is no output verbosity, 3 is maximum verbosity.
recipe.fithooks[0].verbose = 0
