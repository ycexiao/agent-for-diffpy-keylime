"""
Initialize parallelization for  PDF refinement. This script belongs to the
initialize_parallel stage

This script requires:
  - run_parallel variable as the input.

This script provides:
  - run_parallel, ncpu, and pool variables as the output.
"""

# all imports
import numpy
import warnings
from diffpy.srfit.fitbase import FitContribution
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.pdf import PDFParser
from pathlib import Path
from diffpy.structure.parsers import getParser
from pathlib import Path
from diffpy.srfit.pdf import PDFGenerator
from diffpy.structure.parsers import getParser
from pathlib import Path
from diffpy.srfit.pdf import PDFGenerator
from diffpy.srfit.fitbase import FitRecipe
from diffpy.srfit.fitbase.constrainer import constrainAsSpaceGroup

# all external input parameters
run_parallel = True
profile_path = Path("data/Ni.gr").resolve()
structure_path = Path("data/Ni.cif").resolve()
equation_string = "s0*G1"
qmax = None
qmin = None
xmin = None
xmax = None
dx = None
parameter_values_dictionary = {}

# script body
# initialize parallelization stage
if run_parallel:
    try:
        import multiprocessing
        from multiprocessing import Pool

        import psutil

        syst_cores = multiprocessing.cpu_count()
        cpu_percent = psutil.cpu_percent()
        avail_cores = numpy.floor((100 - cpu_percent) / (100.0 / syst_cores))
        ncpu = int(numpy.max([1, avail_cores]))
        pool = Pool(processes=ncpu)
    except ImportError:
        warnings.warn(
            "\nYou don't appear to have the necessary packages for "
            "parallelization. Proceeding without parallelization."
        )
        run_parallel = False
        ncpu = None
        pool = None

# initialize profile stage
profile = Profile()
parser = PDFParser()
parser.parseString(Path(profile_path).read_text())
profile.loadParsedData(parser)
if qmin:
    profile.meta["qmin"] = qmin
if qmax:
    profile.meta["qmax"] = qmax
profile.setCalculationRange(xmin=xmin, xmax=xmax, dx=dx)

# initialize structure stage
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

# initialize contribution stage
contribution = FitContribution("pdfcontribution")
contribution.setProfile(profile)
for pdfgenerator in pdfgenerators:
    contribution.addProfileGenerator(pdfgenerator)
contribution.setEquation(equation_string)

# initialize recipe stage
recipe = FitRecipe()
recipe.addContribution(contribution)
delta1 = getattr(pdfgenerators[0], "delta1")
delta2 = getattr(pdfgenerators[0], "delta2")
s0 = getattr(contribution, "s0")
qdamp = getattr(pdfgenerators[0], "qdamp")
qbroad = getattr(pdfgenerators[0], "qbroad")
recipe.addVar(delta1, name="delta1", fixed=False)
recipe.addVar(delta2, name="delta2", fixed=False)
recipe.addVar(s0, name="s0", fixed=False)
recipe.addVar(qdamp, name="qdamp", fixed=False)
recipe.addVar(qbroad, name="qbroad", fixed=False)
structure_parset = pdfgenerators[0].phase
spacegroupparams = constrainAsSpaceGroup(structure_parset, spacegroups[0])
for par in spacegroupparams.latpars:
    recipe.addVar(par, name=par.name, fixed=False)
for par in spacegroupparams.xyzpars:
    recipe.addVar(par, name=par.name, fixed=False)
for par in spacegroupparams.adppars:
    recipe.addVar(par, name=par.name, fixed=False)
recipe.fix("all")
# 0 is no output verbosity, 3 is maximum verbosity.
recipe.fithooks[0].verbose = 0
recipe.fithooks[0].verbose = 0
for parameter_name, parameter_value in parameter_values_dictionary.items():
    parameter_obj = recipe._parameters.get(parameter_name, None)
    if parameter_obj is not None:
        parameter_obj.setValue(parameter_value)
    else:
        warnings.warn(
            f"Parameter {parameter_name} not found in the recipe. "
            "Skipping setting its initial value."
        )
