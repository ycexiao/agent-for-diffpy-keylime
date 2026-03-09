# Create a FitContribution instance
contribution = FitContribution("crystal")  # "crystal" is the contribution name

# ---

# Add a PDFGenerator to the FitContribution
contribution.addGenerator(
    generator_crystal
)  # generator_crystal is a PDFGenerator instance

# ---

# Add a Profile to the FitContribution
contribution.setProfile(profile, xname="r")  # profile is a Profile instance

# ---

# Set the equation of the FitContribution
# 's1*G1' is the equation. 's1' and 'G1' are parameter names
# Usually 's<number>' will be used as scale factor and 'G<number>' is the generator name.
contribution.setEquation("s1*G1")
