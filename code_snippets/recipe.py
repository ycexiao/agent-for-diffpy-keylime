# Create the FitRecipe instance
recipe = FitRecipe()

# ---

# Add the FitContribution to the FitRecipe
recipe.addContribution(contribution)

# ---

# Set the Qdamp parameter in the recipe
recipe.crystal.G1.qdamp.value = QDAMP_I  # 'crystal' is the contribution name, 'G1' is the generator name, 'qdamp' is the parameter name, and QDAMP_I is the value to set.
# Set the Qbroad parameter in the recipe
recipe.crystal.G1.qbroad.value = QBROAD_I

# ---

# Set the Qmax parameter in the recipe
recipe.crystal.G1.setQmax(QMAX)
# Set the Qmin parameter in the recipe
recipe.crystal.G1.setQmin(QMIN)

# ---

# add the parameter create in the FitContribution instance as the variable in the FitRecipe instance
recipe.addVar(
    contribution.s1, SCALE_I
)  # contribution is the FitContribution instnace, s1 is the parameter appeas in the equation string, SCALE_I is initial value.

# ---

# add symmertry confined parameters as the variable in the FitRecipe instance
spacegroupparams = constrainAsSpaceGroup(
    generator_crystal.phase, sg
)  # generator_crystal is the PDFGenerator instance, sg is the space group number or symbol, e.g. 'F-3m'.
# add lattice parameter variables
for par in spacegroupparams.latpars:
    recipe.addVar(par, fixed=False)
# add adp(Atomic Displacement Parameters) variables
for par in spacegroupparams.adppars:
    recipe.addVar(par, fixed=False)
# add atomic position variables
for par in spacegroupparams.pospars:
    recipe.addVar(par, fixed=False)

# ---

# add delta2 parameter in the PDFGenerator instance as the variable in the FitRecipe instance
recipe.addVar(
    generator_crystal.delta2
)  # generator_crystal is the PDFGenerator instance, delta2 is the parameter name.

# add qdamp and qbroad parameters in the PDFGenerator instance as the variable in the FitRecipe instance
recipe.addVar(generator_crystal.qdamp, fixed=False)
recipe.addVar(generator_crystal.qbroad, fixed=False)
