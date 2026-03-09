# Import libraries and modules required for data fitting and analysis in PDF (Pair Distribution Function) studies.
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

from diffpy.srfit.fitbase import FitContribution, FitRecipe
from diffpy.srfit.fitbase import FitResults
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.pdf import PDFParser, PDFGenerator
from diffpy.structure.parsers import getParser
from diffpy.srfit.structure import constrainAsSpaceGroup

# ---

# Create a CIF file parser to extract the structural and space group information from the specified CIF file.
p_cif = getParser("cif")
stru1 = p_cif.parseFile(cif_path)
sg = p_cif.spacegroup.short_name

# ---

# Create a Profile object for the experimental dataset by parsing the data file and setting the calculation range and mesh points in r-space.
profile = Profile()
parser = PDFParser()
parser.parseFile(dat_path)
profile.loadParsedData(parser)
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# ---

# Create a PDFGenerator object named 'G1' and associate it with the provided structure object (stru1) as a periodic structure for PDF calculation.
generator_crystal1 = PDFGenerator("G1")
generator_crystal1.setStructure(stru1, periodic=True)

# ---

# Configure parallel processing for the PDFGenerator `generator_crystal1`
RUN_PARALLEL = True  # Set this to True to enable parallel processing
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

# ---

# Create a new instance of the FitContribution class with the name 'crystal'.
contribution = FitContribution("crystal")

# ---

# Add the `generator_crystal1` profile generator to the `contribution` instance of `FitContribution`.
contribution.addProfileGenerator(generator_crystal1)

# ---

# Assign the Profile object to the Fit Contribution's experimental profile, using 'r' as the x-variable name.
contribution.setProfile(profile, xname="r")

# ---

# Set the profile equation for the FitContribution based on the specified PDF Generators.
contribution.setEquation("s1*G1")

# ---

# Instantiate a FitRecipe object to manage the details of the fitting process.
recipe = FitRecipe()

# ---

# Add the FitContribution instance to the FitRecipe.
recipe.addContribution(contribution)

# ---

# Set the Q_damp parameter of the PDFGenerator instance G1 to the value of QDAMP_I.
recipe.crystal.G1.qdamp.value = QDAMP_I

# ---

# Set the Q_broad parameter of the PDFGenerator instance G1 to the value of QBROAD_I.
recipe.crystal.G1.qbroad.value = QBROAD_I

# ---

# Set the maximum q-value for the PDFGenerator instance G1.
recipe.crystal.G1.setQmax(QMAX)

# ---

# Set the minimum q-value for the PDFGenerator instance G1.
recipe.crystal.G1.setQmin(QMIN)

# ---

# Add a scale variable to the Fit Recipe instance, initializing it with a specific value and tagging it as "scale".
recipe.addVar(contribution.s1, SCALE_I, tag="scale")

# ---

# Apply space group constraints to the lattice and atomic displacement parameters (ADPs) based on the specified space group.
spacegroupparams = constrainAsSpaceGroup(generator_crystal1.phase, sg)

# ---

# Loop through lattice parameters and add them as variables to the recipe with a specified value, fixed status, name, and tag.
for par in spacegroupparams.latpars:
    recipe.addVar(
        par, value=CUBICLAT_I, fixed=False, name="fcc_Lat", tag="lat"
    )

# ---

# Loop through ADP parameters and add each as a variable to the recipe with the specified initial value, fixed status, name, and tag.
for par in spacegroupparams.adppars:
    recipe.addVar(par, value=UISO_I, fixed=False, name="fcc_ADP", tag="adp")

# ---

# Add unique instrumental parameters to the Fit Recipe with specified names and tags.
recipe.addVar(
    generator_crystal1.delta2, name="Ni_Delta2", value=DELTA2_I, tag="d2"
)

# ---
