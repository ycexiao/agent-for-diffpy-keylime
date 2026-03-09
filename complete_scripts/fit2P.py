"""
Please see notes in Chapter 6 of the 'PDF to the People' book for additonal
explanation of the code.

This Diffpy-CMI script will carry out a structural refinement of a measured
PDF from a sample containing two phases, silicon and nickel.  It is the
same refinement as is done using PDFgui in this chapter of the book, only
this time using Diffpy-CMI.
"""

# 1: Import relevant system packages that we will need...
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

# ... and the relevant CMI packages
from diffpy.srfit.fitbase import FitContribution, FitRecipe
from diffpy.srfit.fitbase import FitResults
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.pdf import PDFParser, PDFGenerator
from diffpy.structure.parsers import getParser
from diffpy.srfit.structure import constrainAsSpaceGroup

# 9: Create two CIF file parsing objects, parse and load the structures, and
# grab the space group names.
p_cif1 = getParser("cif")
p_cif2 = getParser("cif")
stru1 = p_cif1.parseFile(cif_path1)
stru2 = p_cif2.parseFile(cif_path2)
sg1 = p_cif1.spacegroup.short_name
sg2 = p_cif2.spacegroup.short_name

# 10: Create a Profile object for the experimental dataset and
# tell this profile the range and mesh of points in r-space.
profile = Profile()
parser = PDFParser()
parser.parseFile(dat_path)
profile.loadParsedData(parser)
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# 11a: Create a PDF Generator object for a periodic structure model
# of phase 1.
generator_crystal1 = PDFGenerator("G_Si")
generator_crystal1.setStructure(stru1, periodic=True)

# 11b: Create a PDF Generator object for a periodic structure model
# of phase 2.
generator_crystal2 = PDFGenerator("G_Ni")
generator_crystal2.setStructure(stru2, periodic=True)

# 12: Create a Fit Contribution object. This is new, as we
# need to tell the Fit Contribution about BOTH the phase
# represented by 'generator_crystal1' AND the phase represented
# by 'generator_crystal2'.
contribution = FitContribution("crystal")
contribution.addProfileGenerator(generator_crystal1)
contribution.addProfileGenerator(generator_crystal2)

# 13: Set the Fit Contribution profile to the Profile object.
contribution.setProfile(profile, xname="r")

# 14: Set an equation, based on your PDF generators. This is
# a more complicated case, since we have two phases. The equation
# here will be the sum of the contributions from each phase,
# 'G_Si' and 'G_Ni' weighted by a refined scale term for each phase,
# 's1_Si' and '(1 - s1_Si)'. We also include a general 's2'
# to account for data scale.
contribution.setEquation("s2*(s1_Si*G_Si + (1.0-s1_Si)*G_Ni)")

# 15: Create the Fit Recipe object that holds all the details of the fit.
recipe = FitRecipe()
recipe.addContribution(contribution)

# 16: Add, initialize, and tag the two scale variables.
recipe.addVar(contribution.s1_Si, SCALE_I_SI, tag="scale")
recipe.addVar(contribution.s2, DATA_SCALE_I, tag="scale")

# 17:This is new, we want to ensure that the data scale parameter 's2'
# is always positive, and the phase scale parameter 's1_Si' is always
# bounded between zero and one, to avoid any negative PDF signals.
# We do this by adding 'restraints'. Effectively a restrain will modify
# our objective function such that if the parameter approaches a user
# defined upper or lower bound, the objective function will increase,
# driving the fit away from the boundary.
recipe.restrain("s2", lb=0.0, scaled=True, sig=0.00001)

recipe.restrain("s1_Si", lb=0.0, ub=1.0, scaled=True, sig=0.00001)

# 18a: This is a bit new. We will again use the srfit function
# constrainAsSpaceGroup to constrain the lattice and ADP parameters
# according to the space group of each of the two phases.
# We loop through generators composed of PDF Generators
# and space groups specific to EACH of the TWO candidate phases.
# We use 'enumerate' to create an iterating index 'i' such that each
# parameter can get it's own unique name, without colliding parameters.
for name, generator, space_group in zip(
    ["Si", "Ni"], [generator_crystal1, generator_crystal2], [sg1, sg2]
):

    # 18b: Initialize the instrument parameters, Q_damp and Q_broad, and
    # assign Q_max and Q_min for each phase.
    generator.qdamp.value = QDAMP_I
    generator.qbroad.value = QBROAD_I
    generator.setQmax(QMAX)
    generator.setQmin(QMIN)

    # 18c: Get the symmetry equivalent parameters for each phase.
    spacegroupparams = constrainAsSpaceGroup(generator.phase, space_group)
    # 18d: Loop over and constrain these parameters for each phase.
    # Each parameter name gets the loop index 'i' appeneded so there are not
    # parameter name collisions.
    for par in spacegroupparams.latpars:
        recipe.addVar(par, name=f"{par.name}_{name}", fixed=False, tag="lat")
    for par in spacegroupparams.adppars:
        recipe.addVar(par, name=f"{par.name}_{name}", fixed=False, tag="adp")

    # 19: Add delta, but not instrumental parameters to Fit Recipe.
    # One for each phase.
    recipe.addVar(
        generator.delta1,
        name=f"Delta1_{name}",
        value=DELTA1_I_SI,
        tag="d1",
    )
# Tell the Fit Recipe we want to write the maximum amount of
# information to the terminal during fitting.
recipe.fithooks[0].verbose = 3
