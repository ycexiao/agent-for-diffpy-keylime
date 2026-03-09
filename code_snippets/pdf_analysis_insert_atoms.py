# Import the Path class from the pathlib module to facilitate filesystem path manipulation.
from pathlib import Path

# ---

# Import the matplotlib library and its pyplot module to enable plotting functionalities.
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---

# Import the numpy library for efficient numerical computations.
import numpy as np

# ---

# Import the least_squares function from scipy.optimize to perform optimization tasks.
from scipy.optimize import least_squares

# ---

# Import the FitContribution, FitRecipe, and FitResults classes from diffpy.srfit.fitbase for managing refinement contributions, recipes, and results.
from diffpy.srfit.fitbase import FitContribution, FitRecipe
from diffpy.srfit.fitbase import FitResults

# ---

# Import the Profile class from diffpy.srfit.fitbase to manage experimental PDF data profiles effectively.
from diffpy.srfit.fitbase import Profile

# ---

# Import the PDFParser and PDFGenerator classes for parsing and generating Pair Distribution Functions (PDF) from scattering data.
from diffpy.srfit.pdf import PDFParser, PDFGenerator

# ---

# Import the `getParser` function from `diffpy.structure.parsers` to obtain structure file parsers.
from diffpy.structure.parsers import getParser

# ---

# Import the Atom class from the diffpy.structure.atom module to create instances of atoms for structural modeling.
from diffpy.structure.atom import Atom

# ---

# Import the `constrainAsSpaceGroup` function from `diffpy.srfit.structure` to impose symmetry constraints for the structure model based on a specified space group.
from diffpy.srfit.structure import constrainAsSpaceGroup

# ---

# Instantiate a CIF file parser, parse the structure file for structural data, and retrieve the space group name.
p_cif = getParser("cif")
stru1 = p_cif.parseFile(cif_path)
sg = p_cif.spacegroup.short_name

# ---

# Set the anisotropy attribute of the structure object to enable anisotropic behavior.
stru1.anisotropy = True

# ---

# Iterate through all atoms in the structure, and if an atom is of type "Ba", add a new atom of type "K" at the same coordinates; if it is of type "Zn", add a new atom of type "Mn" at the same coordinates.
for atom in stru1:
    if "Ba" in atom.element:
        stru1.addNewAtom(Atom("K", xyz=atom.xyz))
    elif "Zn" in atom.element:
        stru1.addNewAtom(Atom("Mn", xyz=atom.xyz))

# ---

# Instantiate a Profile object to encapsulate properties of an experimental dataset.
profile = Profile()

# ---

# Instantiate a PDFParser to read the PDF data file.
parser = PDFParser()

# ---

# Use the `parseFile` method of the `PDFParser` instance to load data from the specified file path.
parser.parseFile(dat_path)

# ---

# Load parsed data into the Profile instance's attributes, including observed values and metadata.
profile.loadParsedData(parser)

# ---

# Set the epsilon-inclusive calculation range and point mesh in r-space for the Profile instance, adhering to observed data bounds.
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# ---

# Instantiate a PDFGenerator for the periodic structure model with the name "G1".
generator_crystal1 = PDFGenerator("G1")

# ---

# Set the structure for the PDFGenerator instance, specifying that it should be treated as periodic.
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

# Create an instance of the FitContribution class to manage the fit details associated with a specific name, "crystal".
contribution = FitContribution("crystal")

# ---

# Integrate the PDFGenerator instance into the FitContribution instance for profile management.
contribution.addProfileGenerator(generator_crystal1)

# ---

# Assign the Profile object to the FitContribution instance and set the x-axis variable name.
contribution.setProfile(profile, xname="r")

# ---

# Set the profile equation for the FitContribution using the string "s1*G1".
contribution.setEquation("s1*G1")

# ---

# Instantiate a FitRecipe object to handle all contributions for fitting.
recipe = FitRecipe()

# ---

# Add the FitContribution to the FitRecipe to finalize the fitting configuration.
recipe.addContribution(contribution)

# ---

# Initialize the Q_damp and Q_broad parameters of the generator_crystal1 instance, and set the Q_max and Q_min values for the PDF calculations.
generator_crystal1.qdamp.value = QDAMP_I
generator_crystal1.qbroad.value = QBROAD_I
generator_crystal1.setQmax(QMAX)
generator_crystal1.setQmin(QMIN)

# ---

# Initialize the scale variable in the fit recipe with the specified initial value and attach the tag "scale".
recipe.addVar(contribution.s1, SCALE_I, tag="scale")

# ---

# Constrain the lattice and atomic displacement parameters (ADPs) of the generator_crystal1 to match the specified space group and store the resulting parameters in spacegroupparams.
spacegroupparams = constrainAsSpaceGroup(generator_crystal1.phase, sg)

# ---

# Iterate through lattice parameters and add them as unconstrained variables to the recipe, tagging them for identification.
for par in spacegroupparams.latpars:
    recipe.addVar(par, fixed=False, tag="lat")

# ---

# Iterate through ADP parameters and add them as unconstrained variables with the tag "adp" to the recipe.
for par in spacegroupparams.adppars:
    recipe.addVar(par, fixed=False, tag="adp")

# ---

# Iterate through XYZ parameters and add them as unconstrained variables with a tag for fitting.
for par in spacegroupparams.xyzpars:
    recipe.addVar(par, fixed=False, tag="xyz")

# ---

# Add the delta1 parameter from generator_crystal1 to the Fit Recipe as a new variable with the name "Delta1", initial value DELTA1_I, and tag "d1", ensuring it is not treated as an instrumental parameter.
recipe.addVar(
    generator_crystal1.delta1, name="Delta1", value=DELTA1_I, tag="d1"
)

# ---

# Add new variables for the occupancy of Manganese (Mn) and Potassium (K) to the recipe, initializing them with specified values and tagging them as "occs".
recipe.newVar(name="Mn_occ", value=MN_FRAC_I, fixed=True, tag="occs")
recipe.newVar(name="K_occ", value=K_FRAC_I, fixed=True, tag="occs")

# ---

# Apply occupancy constraints to atoms in the structure based on their labels.
for atom in recipe.crystal.G1.phase.atoms:
    if "Ba" in atom.atom.label:
        recipe.constrain(atom.occupancy, "1.0 - K_occ")
    if "K" in atom.atom.label:
        recipe.constrain(atom.occupancy, "K_occ")
    if "Zn" in atom.atom.label:
        recipe.constrain(atom.occupancy, "1.0 - Mn_occ")
    if "Mn" in atom.atom.label:
        recipe.constrain(atom.occupancy, "Mn_occ")

# ---

# Set the verbosity level of the first fitting hook in the FitRecipe to 3 to enable detailed information during the fitting process.
recipe.fithooks[0].verbose = 3

# ---
