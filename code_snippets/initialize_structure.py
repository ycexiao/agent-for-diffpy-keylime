"""
Initialize structures for single phase PDF refinement. This script belongs to
the initialize_structure stage

This script requires:
  - ncpu, pool, and run_parallel variables from initialize_parallel stage.
  - structure_path variable as the input.

This script provides:
  - spacegroups: List[str],
  - pdfgenerators: List[diffpy.srfit.pdf.PDFGenerator]
variables as the output.
"""

# ===========================
# imports
# ===========================
from diffpy.structure.parsers import getParser
from pathlib import Path
from diffpy.srfit.pdf import PDFGenerator
import numpy
import warnings

# ===========================
# input parameters
# ===========================
run_parallel = True
structure_path = Path("data/Ni.cif").resolve()

# ===========================
# Output parameters
# ===========================
spacegroup = None
pdfgenerator = None

# ===========================
# script body
# ===========================
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
stru_parser = getParser("cif")
structure = stru_parser.parse(structure_path.read_text())
sg = getattr(stru_parser, "spacegroup", None)
spacegroup = sg.short_name if sg is not None else "P1"
pdfgenerator = PDFGenerator(f"G1")
pdfgenerator.setStructure(structure)
if run_parallel:
    pdfgenerator.parallel(ncpu=ncpu, mapfunc=pool.map)
