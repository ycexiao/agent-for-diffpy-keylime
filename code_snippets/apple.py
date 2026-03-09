from llama_cloud import LlamaCloud, AsyncLlamaCloud
import os
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from typing import TypedDict, List, Dict, Any
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    AnyMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from pathlib import Path
from typing_extensions import Annotated
from langgraph.graph import add_messages
from langchain.tools import tool
from langgraph.types import interrupt
import json
from pydantic import BaseModel

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

One FitRecipe corresponds to
one or multiple FitContribution(s) depends on the number of experiment PDF datasets and

One PDFContribution corresponds to
one or multiple PDFGenerator(s) depends on the number of structure models involved in the experiment PDF and
One Profile

One PDFGenerator corresponds to
one structure model with many structural parameters.

One structure model corresponds to
one standard structure file (e.g., .cif file) with possible modifications.

One Profile corresponds to
one experiment PDF dataset.

Before Human experts write a refinement script using diffpy.srfit, they typically consider the following aspects:
1. the number of PDF datasets to be refined against.
2. the avaiailable structure files for each phase present in each experiment PDF data.
3. the effects to be considered during the refinemnt: scaling factor, nanoparticle effect, etc.
4. the allowed variations of the structure model parameters during the refinement determined by constraints and restrains.

When Human experts write a refinement script using diffpy.srfit, they typically follow these steps:
1. Initialize_profile stage: Load all experiment PDF data as the diffpy.srfit.fitbase.Profile object(s).
    1. When multiple datasets are present, multiple diffpy.srfit.fitbase.Profile objects are created.
2. Initialize_structure stage: Load corresponding standard structure file(s) and created the diffpy.srfit.pdf.PDFGenerator obeject(s) for each diffpy.srfit.fitbase.Profile object.
    1. When multiple phase are present in one PDF dataset, multiple PDFGenerator objects are created accordingly in that dataset.
    2. When the standard structure file doesn't fully represent the actual structure, modify the internal diffpy.structure.Structure accordingly before creating the PDFGenerator object.
3. Initialize_contribution stage: Create a diffpy.srfit.fitbase.FitContribution object to link the PDFGenerator(s) and the corresponding Profile for each diffpy.srfit.fitbase.Profile object.
    1. Usually scaling factor are considered in this stage.
    2. When nanoparticle effect are present, it's effect is also handled in this stage.
    3. When multiple PDF datasets are present, multiple diffpy.srfit.fitbase.FitContribution objects are created accordingly.
4. Initialize_recipe stage: Create a diffpy.srfit.fitbase.FitRecipe object to manage the overall refinement process.
    1. When there are special constraints (e.g., force two variables in different contributions to be equal), set up the constraints in this stage.
    2. When there are restrains (e.g., bond length restration, ratio is between 0 and 1), set up the restrains in this stage.
"""

sectioning_prompt_template = (
    """
Background knowledge:
{general_knowledge}

You are a silent but helpful internal assistant. 

When all tool calls are finished, only return "All jobs are Done"

Instructions:
1. You are a helpful assistant that segments text into sections based on the background knowledge provided.
2. You should extract all and only these sections:
    1. imports
    2. initialize_profile
    3. initialize_structure
    4. initialize_contribution
    5. initialize_recipe
    6. visualization (optional). Might not be presented in the provided script.
3. You should pay specific attention to the following objects in each sections:
    1. Profile
    2. PDFGenerator
    3. FitContribution
    4. FitRecipe
4. You can not leave any operations or assignments related to these objects.
5. When comments (# and """
    """) are too long (over 50 words), summrize and replace.
6. When comments start with a number, remove the number.

Here is a example of each section:
imports section:
from diffpy.srfit.fitbase import Profile
from diffpy.srfit.pdf import PDFParser
from pathlib import Path

initialize_profile section:
{initialize_profile}

initialize_structure section:
{initialize_structure}

initialize_contribution section:
{initialize_contribution}

initialize_recipe section:
{initialize_recipe}

vizualization section:
{visualization}

Input text:
{text}

Output the results of each section in plain JSON format (without ```json and ```)`
Use the section name as the key in the JSON object. 
Use the string content of each section as the value in the JSON object.
"""
)

canonical_example = Path("canonical_example.py").read_text()
profile_example = Path("initialize_profile.py").read_text()
structure_example = Path("initialize_structure.py").read_text()
contribution_example = Path("initialize_contribution.py").read_text()
recipe_example = Path("initialize_recipe.py").read_text()
Visualization_example = Path("visualize.py").read_text()


@tool
def write_files(filenames: list[str], filecontents: list[str]):
    """
    Write 'filecontents' to 'filenames'. If the file already exists, append a counter to the filename.

    Parameters
    ----------
    filenames : list of str
        The names of the files to write to.
    filecontents : list of str
        The contents to write to the files.

    Returns
    -------
    flag : bool
        True if the files were written successfully, False otherwise.
    """
    for filename, filecontent in zip(filenames, filecontents):
        file_path = Path(filename)
        counter = 1
        while file_path.exists():
            file_path = Path(filename).with_name(
                f"{file_path.stem}_{counter}{file_path.suffix}"
            )
            counter += 1
        if counter > 5:
            return False
        file_path.write_text(filecontent)
        print(f"File written to: {file_path.name}")
    return True


@tool
def read_files(filenames: list[str]) -> tuple[str, bool]:
    """
    Read the content of a file.

    Parameters
    ----------
    filenames : list of str
        The nlist of filenames to read from.

    Returns
    -------
    contents : List of str
        The content of the files
    flag : bools
        True if the file was read successfully, False otherwise.
    """
    contents = []
    for filename in filenames:
        file_path = Path(filename)
        if not file_path.exists():
            return "", False
        contents.append(file_path.read_text())
    return contents, True


@tool
def list_file(folder_path: str) -> tuple[list[str], bool]:
    """
    Get all files inside a directory.

    Parameters
    ----------
    folder_path : str
        The path to the folder to list files from.
    """
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        return [], False
    return [str(f) for f in folder_path.iterdir() if f.is_file()], True


@tool
def write_file(file_content, file_path: str):
    """
    Write file content to a specified file path.

    Parameters
    ----------
    file_content : str
        The content to write to the file.
    file_path : str
        The path to the file to write to.
    """
    file_path = Path(file_path)
    counter = 1
    max_counter = 5
    while file_path.exists():
        if counter > max_counter:
            return (False,)
        file_path = file_path.with_name(
            f"{file_path.stem}_{counter}{file_path.suffix}"
        )
        counter += 1
    file_path.write_text(file_content)
    print(f"File written to: {file_path.name}")
    return (False,)


def toolcall_condition_factory(tool_node_name, otherwise_node_name="END"):
    def toolcall_condition(state):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return tool_node_name
        else:
            return otherwise_node_name

    return toolcall_condition


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    script: str
    sections: List[dict]


class OutputSchema(BaseModel):
    import_: str
    initialize_profile: str
    initialize_structure: str
    initialize_contribution: str
    initialize_recipe: str
    Visualization: str


@tool
def subdivide_into_sections(input_filename: str, output_filesname: str):
    """
    Subdivide a script into sections based on its content and structure.
    The script content is read from the input file.
    The output is written to files with the given name.

    Parameters
    ----------
    input_filename: str
       The path to the script file to be subdivided.
    output_filestem: str
       The filename for the output files.

    Returns
    -------
    success: bool
        True if the script was successfully subdivided, False otherwise.
    """
    if not Path(input_filename).exists():
        return False
    sectioning_prompt = sectioning_prompt_template.format(
        general_knowledge=general_knowledge,
        initialize_profile=profile_example,
        initialize_structure=structure_example,
        initialize_contribution=contribution_example,
        initialize_recipe=recipe_example,
        visualization=Visualization_example,
        text=Path(input_filename).read_text(),
    )
    llm = ChatOpenAI(model="gpt-4o-mini")
    structured_llm = llm.with_structured_output(OutputSchema)
    response = structured_llm.invoke(sectioning_prompt)
    json.dump(response.model_dump(), open(f"{output_filesname}", "w"))
    return True


def agent_node(state):
    prompt = """
    You are a silent but helpful internal assistant. 

    When all tool calls are finished, only return "All jobs are Done"

    Here is a description of the functionalities and corresponding tools you
    have. It is in the format of 'functionality(tool)'
      (1) subdivide a script into sections, and store all sections in one json file
        based on the input and output filename. (subdivide_script)
    """
    llm = ChatOpenAI(model="gpt-4o-mini")
    llm_with_tools = llm.bind_tools([subdivide_into_sections])
    response = llm_with_tools.invoke(
        [SystemMessage(content=prompt)] + state["messages"]
    )
    return {"messages": [response]}


tool_node = ToolNode([subdivide_into_sections])

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", tools_condition)
graph.add_edge("tools", "agent")
graph = graph.compile()
result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="Read the content of example_folder/fitBulkNi.py and subdivide it into sections, and store the outputs in ni.json"
            )
        ]
    }
)
