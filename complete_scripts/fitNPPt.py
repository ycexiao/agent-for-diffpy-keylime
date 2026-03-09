"""
This Diffpy-CMI script will carry out a structural refinement of a measured
PDF from nanocrystalline platinum.
It requires a result file about the bulk platinum to provide initial the instrument parameters.
"""

# 1: Import relevant system packages that we will need...
from pathlib import Path
import re
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

# ... and the relevant CMI packages
from diffpy.srfit.fitbase import (
    FitContribution,
    FitRecipe,
    FitResults,
    Profile,
)
from diffpy.srfit.pdf import PDFParser, PDFGenerator
from diffpy.structure.parsers import getParser
from diffpy.srfit.pdf.characteristicfunctions import sphericalCF
from diffpy.srfit.structure import constrainAsSpaceGroup

# 10: Create a CIF file parsing object, parse and load the structure, and
# grab the space group name.
p_cif = getParser("cif")
stru1 = p_cif.parseFile(cif_path)
sg = p_cif.spacegroup.short_name

# 11: Create a Profile object for the experimental dataset and
# tell this profile the range and mesh of points in r-space.
profile = Profile()
parser = PDFParser()
parser.parseFile(dat_path)
profile.loadParsedData(parser)
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# 12: Create a PDF Generator object for a periodic structure model.
generator_crystal1 = PDFGenerator("G1")
generator_crystal1.setStructure(stru1, periodic=True)

# 13: Create a Fit Contribution object.
contribution = FitContribution("crystal")
contribution.addProfileGenerator(generator_crystal1)

# 14: Set the Fit Contribution profile to the Profile object.
contribution.setProfile(profile, xname="r")

# 15: Set an equation, based on your PDF generators. Here we add an extra layer
# of complexity, incorporating 'f' into our equation. This new term
# incorporates the effect of finite crystallite size damping on our PDF model.
# In this case we use a function which models a spherical NP 'sphericalCF'.
contribution.registerFunction(sphericalCF, name="f")
contribution.setEquation("s1*G1*f")

# 16: Create the Fit Recipe object that holds all the details of the fit.
recipe = FitRecipe()
recipe.addContribution(contribution)

# 17: Initialize the instrument parameters, Q_damp and Q_broad, and
# assign Q_max and Q_min.
generator_crystal1.qdamp.value = QDAMP_I
generator_crystal1.qbroad.value = QBROAD_I
generator_crystal1.setQmax(QMAX)
generator_crystal1.setQmin(QMIN)

# 18: Add, initialize, and tag variables in the Fit Recipe object.
# In this case we also add 'psize', which is the NP size.
recipe.addVar(contribution.s1, SCALE_I, tag="scale")
recipe.addVar(contribution.psize, PSIZE_I, tag="psize")

# 19: Use the srfit function 'constrainAsSpaceGroup' to constrain
# the lattice and ADP parameters according to the Fm-3m space group.
spacegroupparams = constrainAsSpaceGroup(generator_crystal1.phase, sg)
for par in spacegroupparams.latpars:
    recipe.addVar(
        par, value=CUBICLAT_I, fixed=False, name="fcc_Lat", tag="lat"
    )
for par in spacegroupparams.adppars:
    recipe.addVar(par, value=UISO_I, fixed=False, name="fcc_Uiso", tag="adp")

# 20: Add delta, but not instrumental parameters to Fit Recipe.
# The instrumental parameters will remain fixed at values obtained from
# the Ni calibrant in our previous example. As we have not added them through
# recipe.addVar, they cannot be refined.
recipe.addVar(
    generator_crystal1.delta2, name="Pt_Delta2", value=DELTA2_I, tag="d2"
)


# Tell the Fit Recipe we want to write the maximum amount of
# information to the terminal during fitting.
recipe.fithooks[0].verbose = 3
