# Import essential libraries required for the script's functionality.
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

# ---

# Import necessary Diffpy-CMI modules for fitting and analysis tasks.
from diffpy.srfit.fitbase import FitContribution, FitRecipe
from diffpy.srfit.fitbase import FitResults
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.pdf import PDFParser, PDFGenerator
from diffpy.structure.parsers import getParser
from diffpy.srfit.structure import constrainAsSpaceGroup

# ---

# Instantiate two CIF file parsers and parse structure data from the specified CIF file paths.
p_cif1 = getParser("cif")
p_cif2 = getParser("cif")
stru1 = p_cif1.parseFile(cif_path1)
stru2 = p_cif2.parseFile(cif_path2)

# ---

# # Retrieve the short names of the space groups from the parsed structures.
sg1 = p_cif1.spacegroup.short_name
sg2 = p_cif2.spacegroup.short_name

# ---

# Create a Profile object for the experimental dataset, parse the PDF file to load the data, and set the calculation range in r-space.
profile = Profile()
parser = PDFParser()
parser.parseFile(dat_path)
profile.loadParsedData(parser)
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# ---

# Create a PDFGenerator object for a periodic structure model of phase 1 and set the specified structure for PDF calculations.
generator_crystal1 = PDFGenerator("G_Si")
generator_crystal1.setStructure(stru1, periodic=True)

# ---

# Create a PDFGenerator object for a phase 2 model with the name "G_Ni" and set its periodic structure using stru2.
generator_crystal2 = PDFGenerator("G_Ni")
generator_crystal2.setStructure(stru2, periodic=True)

# ---

# Create a FitContribution object named "crystal" to manage the relationship between the experiment PDF dataset and the corresponding structure models.
contribution = FitContribution("crystal")

# ---

# Add the first ProfileGenerator for the corresponding phase to the FitContribution instance.
contribution.addProfileGenerator(generator_crystal1)

# ---

# Add the second profile generator instance for the corresponding phase in the Fit Contribution.
contribution.addProfileGenerator(generator_crystal2)

# ---

# Set the Profile object for the Fit Contribution instance to link the profile data with the experimental PDF data.
contribution.setProfile(profile, xname="r")

# ---

# Set the profile equation for the FitContribution using the string "s2*(s1_Si*G_Si + (1.0-s1_Si)*G_Ni)".
contribution.setEquation("s2*(s1_Si*G_Si + (1.0-s1_Si)*G_Ni)")

# ---

# Instantiate a FitRecipe object to manage the details of the fitting process.
recipe = FitRecipe()

# ---

# Add a FitContribution instance to the FitRecipe.
recipe.addContribution(contribution)

# ---

# Initialize and tag the 'scale' variable for the phase scale parameter 's1_Si'.
recipe.addVar(contribution.s1_Si, SCALE_I_SI, tag="scale")

# ---

# Initialize and assign the scale variable for the data scale parameter 's2'.
recipe.addVar(contribution.s2, DATA_SCALE_I, tag="scale")

# ---

# Ensure the data scale parameter 's2' is constrained to positive values.
recipe.restrain("s2", lb=0.0, scaled=True, sig=0.00001)

# ---

# Ensure the 's1_Si' phase scale parameter is constrained to a range between 0 and 1.
recipe.restrain("s1_Si", lb=0.0, ub=1.0, scaled=True, sig=0.00001)

# ---

# Iterate over two candidate phases to apply constraints on lattice and ADP parameters based on their respective space groups.
for name, generator, space_group in zip(
    ["Si", "Ni"], [generator_crystal1, generator_crystal2], [sg1, sg2]
):
    spacegroupparams = constrainAsSpaceGroup(generator.phase, space_group)
    for par in spacegroupparams.latpars:
        recipe.addVar(par, name=f"{par.name}_{name}", fixed=False, tag="lat")
    for par in spacegroupparams.adppars:
        recipe.addVar(par, name=f"{par.name}_{name}", fixed=False, tag="adp")

# ---

# Loop through two candidate phases to Initialize the damping and broadening parameters, and set the maximum and minimum q-values for the PDF generator.
for name, generator, space_group in zip(
    ["Si", "Ni"], [generator_crystal1, generator_crystal2], [sg1, sg2]
):
    generator.qdamp.value = QDAMP_I
    generator.qbroad.value = QBROAD_I
    generator.setQmax(QMAX)
    generator.setQmin(QMIN)

# ---

# Loop through two candidate phases to add delta1 parameter to Fit Recipe.
for name, generator, space_group in zip(
    ["Si", "Ni"], [generator_crystal1, generator_crystal2], [sg1, sg2]
):
    recipe.addVar(
        generator.delta1,
        name=f"Delta1_{name}",
        value=DELTA1_I_SI,
        tag="d1",
    )

# ---

# Set the verbosity level for output during the fitting process to 3.
recipe.fithooks[0].verbose = 3

# ---
