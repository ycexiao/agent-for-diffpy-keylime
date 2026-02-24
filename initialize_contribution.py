"""
Initialize a single contribution for PDF refinement. This script belongs to
the initialize_contribution stage

This script requires:
  - profile variable from initialize_profile stage.
  - pdfgenerators variable from initialize_structure stage.
  - optional equation_string variable as the input.

This script provides:
  - contribution: diffpy.srfit.fitbase.FitContribution
variables as the output.
"""

from diffpy.srfit.fitbase import FitContribution

# Input parameters
profile = None
pdfgenerators = []
equation_string = "s0*G1"

contribution = FitContribution("pdfcontribution")
contribution.setProfile(profile)
for pdfgenerator in pdfgenerators:
    contribution.addProfileGenerator(pdfgenerator)
contribution.setEquation(equation_string)

# imports
from diffpy.structure.parsers import getParser
from pathlib import Path
from diffpy.srfit.pdf import PDFGenerator

# Input parameters
ncpu = None
pool = None
run_parallel = True
structure_path = Path("data/Ni.cif").resolve()

# script body
spacegroups = []
pdfgenerators = []
stru_parser = getParser("cif")
structure = stru_parser.parse(structure_path.read_text())
sg = getattr(stru_parser, "spacegroup", None)
spacegroup = sg.short_name if sg is not None else "P1"
spacegroups.append(spacegroup)
pdfgenerator = PDFGenerator(f"G1")
pdfgenerator.setStructure(structure)
if run_parallel:
    pdfgenerator.parallel(ncpu=ncpu, mapfunc=pool.map)
pdfgenerators.append(pdfgenerator)
