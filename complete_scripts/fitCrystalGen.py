"""
Please see notes in Chapter 7 of the 'PDF to the People' book for additional
explanation of the code.

This Diffpy-CMI script will carry out a structural refinement of a measured
PDF from Ba0.7K0.3Zn1.7Mn0.3As2.  It is the same refinement as is done using PDFgui in this
chapter of the book, only this time using Diffpy-CMI.
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
from diffpy.structure.atom import Atom
from diffpy.srfit.structure import constrainAsSpaceGroup

# 9: Create a CIF file parsing object, parse and load the structure, and
# grab the space group name.
p_cif = getParser("cif")
stru1 = p_cif.parseFile(cif_path)
sg = p_cif.spacegroup.short_name
stru1.anisotropy = True

# 10 Here we have something new. The cif file we loaded is for BaZn2As,
# But our sample contains K on the Ba site. and Mn on the Zn site.
# we need to add some atoms, so we loop over all atoms in the structure,
# and if the atom element matches "Ba" or "Zn" we add a K or Zn at the same,
# coordinates, respectively.
for atom in stru1:
    if "Ba" in atom.element:
        stru1.addNewAtom(Atom("K", xyz=atom.xyz))
    elif "Zn" in atom.element:
        stru1.addNewAtom(Atom("Mn", xyz=atom.xyz))

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

# 15: Set an equation, based on your PDF generators. This is
# again a simple case, with only a scale and a single PDF generator.
contribution.setEquation("s1*G1")

# 16: Create the Fit Recipe object that holds all the details of the fit.
recipe = FitRecipe()
recipe.addContribution(contribution)

# 17: Initialize the instrument parameters, Q_damp and Q_broad, and
# assign Q_max and Q_min.
generator_crystal1.qdamp.value = QDAMP_I
generator_crystal1.qbroad.value = QBROAD_I
generator_crystal1.setQmax(QMAX)
generator_crystal1.setQmin(QMIN)

# 18: Add, initialize, and tag the scale variable.
recipe.addVar(contribution.s1, SCALE_I, tag="scale")

# 19: Use the srfit function constrainAsSpaceGroup to constrain
# the lattice and ADP parameters according to the I4/mmm space group setting.
spacegroupparams = constrainAsSpaceGroup(generator_crystal1.phase, sg)

for par in spacegroupparams.latpars:
    recipe.addVar(par, fixed=False, tag="lat")
for par in spacegroupparams.adppars:
    recipe.addVar(par, fixed=False, tag="adp")
for par in spacegroupparams.xyzpars:
    recipe.addVar(par, fixed=False, tag="xyz")

# 20: Add delta, but not instrumental parameters to Fit Recipe.
recipe.addVar(
    generator_crystal1.delta1, name="Delta1", value=DELTA1_I, tag="d1"
)

# 21: This is also new. We would like to refine the occupancy of
# both Mn and K, so we need to add two new parameters, here called
# 'Mn_occ' and 'K_occ.' We give them the tag 'occs' and we initialize
# them with reasonable values as defined above.
recipe.newVar(name="Mn_occ", value=MN_FRAC_I, fixed=True, tag="occs")
recipe.newVar(name="K_occ", value=K_FRAC_I, fixed=True, tag="occs")

# 22: Now, we want to constrain the occupancy of sites appropriately.
# To do this, we loop over all atoms in the structure, and if the
# atom label matches a pattern, we constrain the occuapncy appropriately.
for atom in recipe.crystal.G1.phase.atoms:
    if "Ba" in atom.atom.label:
        recipe.constrain(atom.occupancy, "1.0 - K_occ")
    if "K" in atom.atom.label:
        recipe.constrain(atom.occupancy, "K_occ")
    if "Zn" in atom.atom.label:
        recipe.constrain(atom.occupancy, "1.0 - Mn_occ")
    if "Mn" in atom.atom.label:
        recipe.constrain(atom.occupancy, "Mn_occ")

# Tell the Fit Recipe we want to write the maximum amount of
# information to the terminal during fitting.
recipe.fithooks[0].verbose = 3
