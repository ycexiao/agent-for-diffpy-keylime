# create a PDFGenerator instance
generator_crystal = PDFGenerator("G1")  # G1 is the generator name

# ---

# set the structure
generator_crystal.setStructure(
    structure, periodic=True
)  # structure is a diffpy.structure.Structure instance
