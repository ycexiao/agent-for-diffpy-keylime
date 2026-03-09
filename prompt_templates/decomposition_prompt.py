from agent.prompt_templates.general_knowledge import general_knowledge
from pathlib import Path

example_dir = Path(__file__).parents[1] / "examples"
profile_example_path = example_dir / "profile_example.py"
structure_example_path = example_dir / "structure_example.py"
contribution_example_path = example_dir / "contribution_example.py"
recipe_example_path = example_dir / "recipe_example.py"
Visualization_example_path = example_dir / "visualization_example.py"

profile_example = profile_example_path.read_text()
structure_example = structure_example_path.read_text()
contribution_example = contribution_example_path.read_text()
recipe_example = recipe_example_path.read_text()
Visualization_example = Visualization_example_path.read_text()

decomposition_system_prompt = """
Background knowledge:
{general_knowledge}

Instructions:
1. You are a helpful assistant that segments text into sections based on the background knowledge provided.
2. In most cases, the provided script contains the following sections:
    1. imports
    2. initialize_profile
    3. initialize_structure
    4. initialize_contribution
    5. initialize_recipe
    6. visualization (optional). Might not be presented in the provided script.

Here is the functions, objects and their methods/attributes we cares:
1. Profile  (initialize_profile section)
    1. profile.loadParsedData
    2. profile.setCalculationRange
2. diffpy.srfit.pdf.PDFGenerator  (initialize_structure section)
    1. PDFGenerator.setStructure
    2. PDFGenerator.parallel
    3. PDFGenerator.phase
3. diffpy.srfit.fitbase.FitContribution  (initialize_contribution section)
    1. FitContribution.addProfileGenerator
    2. FitContribution.setProfile
    3. FitContribution.setEquation
4. diffpy.srfit.fitbase.FitRecipe  (initialize_recipe section)
    1. FitRecipe.addContribution
    2. FitRecipe.<contribution_name>.<generator_name>.<parameter_name>
    3. FitRecipe.<contribution_name>.<generator_name>.setQmax
    4. FitRecipe.<contribution_name>.<generator_name>.setQmin
    5. FitRecipe.addVar
5. diffpy.srfit.fitbase.constrainer.constrainAsSpaceGroup  (initialize_recipe section)
If they are presented in the provided script, please make sure to use them.
If there are comments around these objects or methods, please make sure to keep them.

Here is a example of each section:
imports section:
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.pdf import PDFParser
from pathlib import Path

initialize_profile section:
{profile_example}

initialize_structure section:
{structure_example}

initialize_contribution section:
{contribution_example}

initialize_recipe section:
{recipe_example}

vizualization section:
{Visualization_example}
"""
