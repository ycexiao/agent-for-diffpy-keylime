"""
This Diffpy-CMI script will carry out a structural refinement of a measured
PDF from nickel.
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

# 9: Create a CIF file parsing object, and use it to parse out
# relevant info and load the structure in the CIF file. This
# includes the space group of the structure. We need this so we
# can constrain the structure parameters later on.
p_cif = getParser("cif")
stru1 = p_cif.parseFile(cif_path)
sg = p_cif.spacegroup.short_name

# 10: Create a Profile object for the experimental dataset.
# This handles all details about the dataset.
# We also tell this profile the range and mesh of points in r-space.
# The 'PDFParser' function should parse out the appropriate Q_min and
# Q_max from the *.gr file, if the information is present.
profile = Profile()
parser = PDFParser()
parser.parseFile(dat_path)
profile.loadParsedData(parser)
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# 11: Create a PDF Generator object for a periodic structure model.
# Here we name it arbitrarily 'G1' and we give it the structure object.
# This Generator will later compute the model PDF for the structure
# object we provide it here.
generator_crystal1 = PDFGenerator("G1")
generator_crystal1.setStructure(stru1, periodic=True)

# 12: Create a Fit Contribution object, and arbitrarily name it 'crystal'.
# We then give the PDF Generator object we created just above
# to this Fit Contribution object. The Fit Contribution holds
# the equation used to fit the PDF.
contribution = FitContribution("crystal")
contribution.addProfileGenerator(generator_crystal1)

# If you have a multi-core computer (you probably do),
# run your refinement in parallel!
# Here we just make sure not to overload your CPUs.
if RUN_PARALLEL:
    try:
        import psutil
        import multiprocessing
        from multiprocessing import Pool
    except ImportError:
        print(
            "\nYou don't appear to have the necessary packages for parallelization"
        )
    syst_cores = multiprocessing.cpu_count()
    cpu_percent = psutil.cpu_percent()
    avail_cores = np.floor((100 - cpu_percent) / (100.0 / syst_cores))
    ncpu = int(np.max([1, avail_cores]))
    pool = Pool(processes=ncpu)
    generator_crystal1.parallel(ncpu=ncpu, mapfunc=pool.map)

# 13: Set the experimental profile, within the Fit Contribution object,
# to the Profile object we created earlier.
contribution.setProfile(profile, xname="r")

# 14: Set an equation, within the Fit Contribution, based on your PDF
# Generators. Here we simply have one Generator, 'G1', and a scale variable,
# 's1'. Using this structure is a very flexible way of adding additional
# Generators (ie. multiple structural phases), experimental Profiles,
# PDF characteristic functions (ie. shape envelopes), and more.
contribution.setEquation("s1*G1")

# 15: Create the Fit Recipe object that holds all the details of the fit,
# defined in previous lines above. We give the Fit Recipe the Fit
# Contribution we created earlier.
recipe = FitRecipe()
recipe.addContribution(contribution)

# 16: Initialize the instrument parameters, Q_damp and Q_broad, and
# assign Q_max and Q_min, all part of the PDF Generator object.
# It's possible that the 'PDFParse' function we used above
# already parsed out ths information, but in case it didn't, we set it
# explicitly again here.
# All parameter objects can have their value assigned using the
# below '.value = ' syntax.
recipe.crystal.G1.qdamp.value = QDAMP_I
recipe.crystal.G1.qbroad.value = QBROAD_I
recipe.crystal.G1.setQmax(QMAX)
recipe.crystal.G1.setQmin(QMIN)

# 17: Add a variable to the Fit Recipe object, initialize the variables
# with some value, and tag it with an aribtrary string. Here we add the scale
# parameter from the Fit Contribution. The '.addVar' method can be
# used to add variables to the Fit Recipe.
recipe.addVar(contribution.s1, SCALE_I, tag="scale")

# 18: Configure some additional fit variables pertaining to symmetry.
# We can use the srfit function 'constrainAsSpaceGroup' to constrain
# the lattice and ADP parameters according to the Fm-3m space group.
# First we establish the relevant parameters, then we loop through
# the parameters and activate and tag them. We must explicitly set the
# ADP parameters using 'value=' because CIF had no ADP data.
spacegroupparams = constrainAsSpaceGroup(generator_crystal1.phase, sg)
for par in spacegroupparams.latpars:
    recipe.addVar(
        par, value=CUBICLAT_I, fixed=False, name="fcc_Lat", tag="lat"
    )
for par in spacegroupparams.adppars:
    recipe.addVar(par, value=UISO_I, fixed=False, name="fcc_ADP", tag="adp")

# 19: Add delta and instrumental parameters to Fit Recipe.
# These parameters are contained as part of the PDF Generator object
# and initialized with values as defined in the opening of the script.
# We give them unique names, and tag them with relevant strings.
recipe.addVar(
    generator_crystal1.delta2, name="Ni_Delta2", value=DELTA2_I, tag="d2"
)

recipe.addVar(
    generator_crystal1.qdamp,
    fixed=False,
    name="Calib_Qdamp",
    value=QDAMP_I,
    tag="inst",
)

recipe.addVar(
    generator_crystal1.qbroad,
    fixed=False,
    name="Calib_Qbroad",
    value=QBROAD_I,
    tag="inst",
)

# Tell the Fit Recipe we want to write the maximum amount of
# information to the terminal during fitting.
# Passing '2' or '1' prints intermediate info, while '0' prints no info.
recipe.fithooks[0].verbose = 3
