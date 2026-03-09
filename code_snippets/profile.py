# create a Profile instance
profile = Profile()

# ---

# load experimental data into a Profile instance
pdf_parser = PDFParser()
pdf_parser.parse("experimental_data.gr")  # path to the experimental data file
profile.loadParsedData(pdf_parser)

# ---

# set the calculation range
# min r value, max r value, and r step.
profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)
