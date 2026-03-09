"""
Please see notes in Chapter 3 of the 'PDF to the People' book for further
explanation of the code.

This Diffpy-CMI script will carry out a structural refinement of a measured
PDF from nanocrystalline zirconium phenyl-phosphonate-phosphate UMOF.  It
is the same refinement as is done using PDFgui in this chapter of the book,
only this time using Diffpy-CMI
"""

# 1: Import relevant system packages that we will need...
import os
import numpy as np
from pyobjcryst.crystal import CreateCrystalFromCIF
from scipy.optimize import least_squares
import matplotlib as mpl
import matplotlib.pyplot as plt

# ... and the relevant CMI packages
from diffpy.srfit.pdf import DebyePDFGenerator, DebyePDFGenerator, PDFParser
from diffpy.srfit.pdf.characteristicfunctions import sphericalCF
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.fitbase import FitContribution, FitRecipe
from diffpy.srfit.fitbase import FitResults

from diffpy.Structure import Structure
from diffpy.srfit.fitbase.fithook import PlotFitHook

structure = Structure(stru_file)

# Create a Profile object for the experimental dataset and
# tell this profile the range and mesh of points in r-space.
profile = Profile()
parser = PDFParser()
parser.parseFile(data_file)
profile.loadParsedData(parser)
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

# Create a PDF Generator object for a periodic structure model.
generator_crystal = DebyePDFGenerator("G_crystal")
generator_crystal.setStructure(structure, periodic=True)

# Generate PDF fit function:
contribution = FitContribution("crystal")
contribution.addProfileGenerator(generator_crystal)
contribution.setProfile(profile, xname="r")
contribution.registerFunction(sphericalCF, name="f")
contribution.setEquation("scale * f * (G_crystal)")

# Create the Fit Recipe object that holds all the details of the fit.
recipe = FitRecipe()
recipe.addContribution(contribution)

# Experimental parameters:
generator_crystal.setQmax(QMAX)
# generator_crystal.setQmin(0.0) # set to zero for bulk material
generator_crystal.qdamp.value = QDAMP_I
generator_crystal.qbroad.value = QBROAD_I

# Profile parameters:
recipe.addVar(contribution.scale, SCALE_I, tag="scale")
recipe.addVar(contribution.psize, PSIZE_I, tag="psize")

# Lattice parameters:
phase_crystal = generator_crystal.phase
lat = phase_crystal.getLattice()
recipe.addVar(lat.a, value=LAT_A_I, tag="lat")
recipe.addVar(lat.b, value=LAT_B_I, tag="lat")
recipe.addVar(lat.c, value=LAT_C_I, tag="lat")
recipe.addVar(lat.beta, value=LAT_BETA_I, tag="lat")

# Thermal parameters (ADPs):
atoms = phase_crystal.getScatterers()
recipe.newVar("Zr_U11", UISO_I, tag="adp")
recipe.newVar("P_U11", UISO_I, tag="adp")
recipe.newVar("O_U11", UISO_I, tag="adp")

for atom in atoms:
    if atom.element.title() == "Zr":
        recipe.constrain(atom.Uiso, "Zr_U11")
    elif atom.element.title() == "P":
        recipe.constrain(atom.Uiso, "P_U11")
    elif atom.element.title() == "O":
        recipe.constrain(atom.Uiso, "O_U11")

# Correlated motion parameter:
recipe.addVar(
    generator_crystal.delta1,
    name="delta1_crystal",
    value=DELTA1_I,
    tag="d1",
)
