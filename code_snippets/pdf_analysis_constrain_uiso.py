# Import essential libraries for file operations, numerical analysis, and data visualization.
import os
import numpy as np
from pyobjcryst.crystal import CreateCrystalFromCIF
from scipy.optimize import least_squares
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---

# Import necessary CMI packages for PDF generation and analysis, including classes for calculating the Pair Distribution Function (PDF) and managing fitting processes.
from diffpy.srfit.pdf import DebyePDFGenerator, PDFParser
from diffpy.srfit.pdf.characteristicfunctions import sphericalCF
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.fitbase import FitContribution, FitRecipe
from diffpy.srfit.fitbase import FitResults

# ---

# Import libraries for structure handling and fitting visualization.
from diffpy.Structure import Structure
from diffpy.srfit.fitbase.fithook import PlotFitHook

# ---

# Load the structure data from the specified file for further processing in PDF calculations.
structure = Structure(stru_file)

# ---

# Instantiate a Profile object for analyzing the experimental dataset.
profile = Profile()

# ---

# Load experimental PDF data from the specified file into the profile using the PDFParser.
parser = PDFParser()
parser.parseFile(data_file)
profile.loadParsedData(parser)

# ---

# Set the epsilon-inclusive calculation range for the Profile object, ensuring it adheres to the observed data points.
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# ---

# Create a DebyePDFGenerator object to compute the Pair Distribution Function for the specified periodic structure model named "G_crystal".
generator_crystal = DebyePDFGenerator("G_crystal")

# ---

# Set the structure for the PDF generator, linking it with the periodic model to facilitate PDF calculations.
generator_crystal.setStructure(structure, periodic=True)

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

# Create a `FitContribution` object named "crystal" to store fit contribution details.
contribution = FitContribution("crystal")

# ---

# Attach the ProfileGenerator to the FitContribution object.
contribution.addProfileGenerator(generator_crystal)

# ---

# Assign the created profile instance to the FitContribution object for analysis.
contribution.setProfile(profile, xname="r")

# ---

# Register the spherical correlation function in the FitContribution.
contribution.registerFunction(sphericalCF, name="f")

# ---

# Set the profile equation for the FitContribution, which will be used to generate the residual for this contribution.
contribution.setEquation("scale * f * (G_crystal)")

# ---

# Instantiate a FitRecipe object to handle the entire fitting process and its details.
recipe = FitRecipe()

# ---

# Add a FitContribution instance to the FitRecipe.
recipe.addContribution(contribution)

# ---

# Set the maximum scattering vector (q-value) for the PDFGenerator instance.
generator_crystal.setQmax(QMAX)

# ---

# Set the Q damping value for the generator crystal instance to the specified QDAMP_I constant.
generator_crystal.qdamp.value = QDAMP_I

# ---

# Set the Q broadening parameter for the PDFGenerator instance.
generator_crystal.qbroad.value = QBROAD_I

# ---

# Add a variable for the contribution scale to the recipe with the specified initial value and tag.
recipe.addVar(contribution.scale, SCALE_I, tag="scale")

# ---

# Add a variable for the contribution particle size to the recipe, initializing it with the specified value and tag.
recipe.addVar(contribution.psize, PSIZE_I, tag="psize")

# ---

# Retrieve the lattice parameters from the phase of the generator crystal instance.
phase_crystal = generator_crystal.phase
lat = phase_crystal.getLattice()

# ---

# Add the lattice parameters a, b, c, and beta to the recipe with the specified initial values and tag them as "lat".
recipe.addVar(lat.a, value=LAT_A_I, tag="lat")
recipe.addVar(lat.b, value=LAT_B_I, tag="lat")
recipe.addVar(lat.c, value=LAT_C_I, tag="lat")
recipe.addVar(lat.beta, value=LAT_BETA_I, tag="lat")

# ---

# Retrieve scatterers from the phase crystal and define new variables for their isotropic thermal parameters.
atoms = phase_crystal.getScatterers()
recipe.newVar("Zr_U11", UISO_I, tag="adp")
recipe.newVar("P_U11", UISO_I, tag="adp")
recipe.newVar("O_U11", UISO_I, tag="adp")

# ---

# Apply specific constraints to the Uiso parameter of each atom based on its element type (Zr, P, O).
for atom in atoms:
    if atom.element.title() == "Zr":
        recipe.constrain(atom.Uiso, "Zr_U11")
    elif atom.element.title() == "P":
        recipe.constrain(atom.Uiso, "P_U11")
    elif atom.element.title() == "O":
        recipe.constrain(atom.Uiso, "O_U11")

# ---

# Add a correlated motion variable named "delta1_crystal" with an initial value of DELTA1_I to the recipe.
recipe.addVar(
    generator_crystal.delta1,
    name="delta1_crystal",
    value=DELTA1_I,
    tag="d1",
)

# ---
