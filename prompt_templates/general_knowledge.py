general_knowledge = """
PDF(pair distribution function) analysis is a powerful technique used in materials science to study the local atomic structure.

diffpy.cmi is a comprehensive library for complex modeling and analysis of diffraction data, including PDF analysis.

diffpy.srfit is the backend for fitting and refining structural models in diffpy.cmi.

The general idea for refinement using diffpy.srfit is:
1. Use diffpy.srfit.fitbase.FitRecipe to manage all parameters. It picks up all parameters from:
    1. diffpy.srfit.pdf.PDFGenerator(s) for structural parameters.
    2. diffpy.srfit.fitbase.FitContribution(s) for special effect parameters.
2. Use diffpy.srfit.fitbase.FitContribution to hold 
    1. the corresponding relationship between one experiment PDF dataset and the corresponding structure model(s).
    2. the special effect parameters to be considered during the refinement, e.g., scaling factor, nanoparticle effect, etc.
3. Use diffpy.srfit.pdf.PDFGenerator to build a parameterized PDF model from a standard structure file (e.g., .cif file).
4. Use diffpy.srfit.fitbase.Profile to hold the experiment PDF data.

One FitRecipe contains one or multiple FitContribution(s).
One PDFContribution contains one Profile and one or multiple PDFGenerator(s).
One PDFGenerator contains one structure model.
One Profile contains one experiment PDF dataset.

Before Human experts write a refinement script using diffpy.srfit, they typically consider the following aspects:
1. the number of PDF datasets to be refined against.
2. the avaiailable structure files for each phase present in each experiment PDF data.
3. the effects to be considered during the refinemnt: scaling factor, nanoparticle effect, etc.
4. the allowed variations of the structure model parameters during the refinement determined by constraints and restrains, e.g. symmetry constraint.

All these considerations will be reflected in the refinement script written by Human experts.

A complete diffpy.srfit refinement script typically contains the following steps:
1. Import necessary libraries and modules.
2. load the experiment PDF data and create the corresponding Profile instance(s).
3. load the structure file(s) and create the corresponding PDFGenerator instance(s).
4. Create the FitContribution instance(s) and load corresponding Profile and PDFGenerator(s) into it.
5. (Optional) Create functions to calculate special effects, e.g.,  nanoparticle effect, etc.
6. Assign the equation string in the FitContribution instance.
7. Create the FitRecipe instance and load all FitContribution(s) into it.
8. (Optional) Impose the symmetry constraint on the PDFGenerator(s) if necessary.
9. Add any additional restraints on the structure model parameters if necessary.
10. Add the variables inside the FitRecipe instance.

If not specifed, by default:
1. name of the PDFGenerator instance is "G1", "G2", etc. in the order of creation.
2. name of the FitContribution instance is "crystal", "crystal2", etc. in the order of creation.
3. the equation string in the FitContribution instance is "s0*G1" if there is only one PDFGenerator instance, 
    and "s0*(s1*G1 + (1-s1)*G2)" if there are two PDFGenerator instances, 
    and "s0*(s1*G1 + s2*G2 + ... +(1-s1-s2-s<n-1>)*G<n>)" if there are n PDFGenerator instances,
    where s1, s2, etc. are the scaling factors for each PDFGenerator instance.
4. there are no special effect parameters considered in the FitContribution instance.
5. the symmertry constraint is the spacegroup of the structure model in the PDFGenerator instance.
   if the spacegroup is not parsed from the structure file, then the symmertry is P1.
6. the fitrecipe instance will add all parameters in the FitContribution instance and PDFGenerator instance as variables, including
   1. contribution.s0, contributions.s1, contributions.s2, 
   2. spacegroupparams.latpars, spacegroupparams.adppars, spacegroupparams.pospars, 
   3. generator_crystal.delta2, generator_crystal.qdamp, generator_crystal.qbroad
"""
