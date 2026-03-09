# Import necessary packages for handling file paths, data manipulation, and plotting.
from pathlib import Path
import re
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

# --- 

# Import necessary Diffpy-SRFit modules for performing the refinement process.
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

# --- 

# Create a CIF file parser, load the structure from the specified CIF file, and extract the space group's short name.
p_cif = getParser("cif")
stru1 = p_cif.parseFile(cif_path)
sg = p_cif.spacegroup.short_name

# --- 

# Create a Profile object and configure its calculation parameters using data extracted from a PDF file.
profile = Profile()
parser = PDFParser()
parser.parseFile(dat_path)
profile.loadParsedData(parser)
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# --- 

# Create a PDFGenerator object with the name "G1" and set its structure to stru1 as periodic.
generator_crystal1 = PDFGenerator("G1")
generator_crystal1.setStructure(stru1, periodic=True)

# --- 

# Create a `FitContribution` object named "crystal" and associate it with the `ProfileGenerator` instance `generator_crystal1`.
contribution = FitContribution("crystal")
contribution.addProfileGenerator(generator_crystal1)

# --- 

# Assign the specified Profile object to the Fit Contribution for subsequent analysis.
contribution.setProfile(profile, xname="r")

# --- 

# Register the `sphericalCF` function as a function named 'f' in the contribution instance.
contribution.registerFunction(sphericalCF, name="f")

# --- 

# Set the profile equation for the contribution instance using the PDF generator and the registered function.
contribution.setEquation("s1*G1*f")

# --- 

# Instantiate a FitRecipe object for managing the fitting process.
recipe = FitRecipe()

# --- 

# Add a `FitContribution` instance to the `FitRecipe`.
recipe.addContribution(contribution)

# --- 

# Configure the damping and broadening parameters for the crystal generator and set the maximum and minimum q-values.
generator_crystal1.qdamp.value = QDAMP_I
generator_crystal1.qbroad.value = QBROAD_I
generator_crystal1.setQmax(QMAX)
generator_crystal1.setQmin(QMIN)

# --- 

# Add 's1' and 'psize' as variables to the Fit Recipe instance with appropriate values and tags.
recipe.addVar(contribution.s1, SCALE_I, tag="scale")
recipe.addVar(contribution.psize, PSIZE_I, tag="psize")

# --- 

# Constrain lattice and atomic displacement parameters (ADPs) according to the Fm-3m space group using the `constrainAsSpaceGroup` function.
spacegroupparams = constrainAsSpaceGroup(generator_crystal1.phase, sg)

# --- 

# Iterate over lattice parameters and add them as variables to the Fit Recipe with specified initial values and tags.
for par in spacegroupparams.latpars:
    recipe.addVar(
        par, value=CUBICLAT_I, fixed=False, name="fcc_Lat", tag="lat"
    )

# --- 

# Iterate over ADP parameters and add them to the Fit Recipe with specified values, names, and tags to enable refinement.
for par in spacegroupparams.adppars:
    recipe.addVar(par, value=UISO_I, fixed=False, name="fcc_Uiso", tag="adp")

# --- 

# Add a delta parameter named "Pt_Delta2" with initial value DELTA2_I to the Fit Recipe.
recipe.addVar(
    generator_crystal1.delta2, name="Pt_Delta2", value=DELTA2_I, tag="d2"
)

# --- 

