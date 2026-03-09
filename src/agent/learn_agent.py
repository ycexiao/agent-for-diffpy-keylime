from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
    AIMessage,
    BaseMessage,
)
from langgraph.graph import add_messages
from typing import TypedDict, List, Literal
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from langgraph.types import Command
from langgraph.graph import MessagesState
from langchain.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
from langgraph.types import interrupt


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

# skeleton_vectorstore = FAISS.load_local(
#     "skeleton_vectorstore", embeddings, allow_dangerous_deserialization=True
# )
# code_vectorstore = FAISS.load_local(
#     "code_vectorstore",
#     embeddings,
#     allow_dangerous_deserialization=True,
# )
docstring_vectorstore = FAISS.load_local(
    "docstring_vectorstore",
    embeddings,
    allow_dangerous_deserialization=True,
)
general_knowledge = Path("prompt_templates/general_knowledge.py").read_text()
standard_example = Path("standard_example.py").read_text()
# -----------------------------------------------------------------------------


class UnderstandingUnit(BaseModel):
    intention: str = Field(
        description="The intention of the corresponding code snippet。"
    )
    implementation: str = Field(
        description="The code implementation of the corresponding intention."
    )


class UnderstandingSchema(BaseModel):
    units: List[UnderstandingUnit] = Field(
        description="The units that compose the python script"
    )


class LearningState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    filepath: str
    units: List[UnderstandingUnit]
    memory_folder: str


def decomposing_node(state):
    llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
    system_prompt = """
    You are a helpful assistant that can understand the implementation purpose 
    (intentions) of every lines of the code script provided.

    You should return todo's based on the purpose (intention) of every lines
    in the python code and the corresponding code snippets. 

    Here are example of how to generate the queries based on the code:
    e.g.
    Create <instance> of <class> with <arguments>.
    Load <input> and create <instance>.
    Use <function> to process <input> and get <output>.
    Use <method> of <instance> of a <class> to process <input> and get <output>.

    You should not break the meaningful code unit into pieces.
    A meaningful code unit is a piece of code that:
    1. appears together without being separated by any empty line
    2. the instances/variables created in the previous line are 
       used immediately in the next 1-3 lines, and then the old instances/variables 
       are not used anymore in the following lines.

    When a few lines are closely related, the variables created in the
    first few lines are used in the following lines immediately, and then
    these variables are not used anymore. Then these lines should be processed 
    together, and only one query should be generated for these lines.
    e.g.
    line 1: instance_name = class_name(<arguments>)
    line 2: instance_name.method(<arguments>)
    line 3: another_instance = another_class(instance_name, <arguments>)
    and then `instance_name` is not used anymore in the following lines. Then 
    these three lines should be processed together. The code block can be

    The lines that creates indentation (which ends with `:`), and the following
    lines under that indentation belongs to the same meaningful unit.
    e.g.
    line 1: for i in range(10):
    line 2:     print(i)
    In this case, line 1 and line 2 should be processed together, 
    and only one query should be generated for these two lines.
    The indentation could be nested, and the first indentation determines
    the code unit.
    line 1 : for i in range(10):
    line 2 :     if i % 2 == 0:
    line 3 :         print(i)
    line 4 :     print(i)
    In this case, line 1, 2, 3 and 4 should be processed together.

    Don't include any markdown format like ```python ``` in the response, 
    just give the pure intention and code snippet.
"""
    script = Path(state["filepath"]).read_text()
    chunks = splitter.split_text(script)
    llm = ChatOpenAI(model="gpt-4o-mini")
    llm_with_structure_output = llm.with_structured_output(UnderstandingSchema)
    response_dict = {"units": []}
    for chunk in chunks:
        messages = [
            SystemMessage(content=general_knowledge + "\n" + system_prompt),
            HumanMessage(content="\nHere is the script:\n" + chunk),
        ]
        response = llm_with_structure_output.invoke(messages)
        units = response.model_dump()["units"]
        response_dict["units"].extend(units)
    # remove duplicated units caused by the overlapping in the chunks
    codes = []
    duplicated_index = []
    for i, unit in enumerate(response_dict["units"]):
        code = unit["implementation"]
        if code in codes:
            duplicated_index.append(i)
        else:
            codes.append(code)
    for i in sorted(duplicated_index, reverse=True):
        del response_dict["units"][i]
    return {"units": response_dict["units"]}


def associating_node(state):
    system_prompt = """
    You are a helpful assistant that can refine the comments of a python script.

    You will be givenseveral lines of python code, a comment that explain it's purpose (intention)
    and several docstring about the functions/classes appeared in the code. The docstring might
    or might not be relevant to the code snippet. 
    
    intention (purpose) as the comment:
    {intention}

    implementation (code snippet):
    {implementation}

    Here are some docstring that might be relevant to the code snippet:
    {docstrings}

    You should only give the refined comment without any additional explanation. 
    The refined comment should be concise and clear, 
    and should accurately reflect the purpose of the code snippet.

    You should not include the code snippet in the response.

    Don't include any markdown format like ```python ``` in the response, 
    just give the pure intention and code snippet.
    """
    global docstring_vectorstore
    llm = ChatOpenAI(model="gpt-4o-mini")
    for i, unit in enumerate(state["units"]):
        query = (
            "Here is the code snippet:\n"
            + unit["implementation"]
            + "Given the code snippet, retrieve relevant docstring that can help understand the code"
        )
        docs = docstring_vectorstore.similarity_search(query, k=3)
        docstrings = "\n".join([doc.page_content for doc in docs])
        message = SystemMessage(
            content=system_prompt.format(
                intention=unit["intention"],
                implementation=unit["implementation"],
                docstrings=docstrings,
            )
        )
        response = llm.invoke([message])
        state["units"][i]["intention"] = response.content

    return state


def memorizing_node(state):
    llm = ChatOpenAI(model="gpt-4o-mini")
    system_prompt = """
You are a helpful assistant come up with file names based on the file content.

The file content is a python script to do PDF (pair distribution function), you
should not focus on the detail implementation of the code,  but should focus 
on the technique/purpose/workflow variation from the standard, trivial 
diffpy.srfit script, which will be provided below

The standard diffpy.srfit script is like this:
{standard_example}

The file content is
{current_script}

Here are the already existing files in the memory folder:
{existing_files}

Don't come up with duplicated file names. 

You should keep the file names concise and informative. The filename should
end with `.py`.
"""

    class OutputSchema(BaseModel):
        code_filename: str = Field(
            description="The file name for storing the code units."
        )

    structured_llm = llm.with_structured_output(OutputSchema)
    if state["memory_folder"]:
        existing_files = "\n".join(
            [f.name for f in Path(state["memory_folder"]).iterdir()]
        )
    else:
        existing_files = "\n".join(
            [f.name for f in Path().iterdir() if f.is_file()]
        )

    code = ""
    for unit in state["units"]:
        code += f"# {unit['intention']}\n"
        code += unit["implementation"]
        code += "\n\n# --- \n\n"
    response = structured_llm.invoke(
        [
            SystemMessage(
                content=system_prompt.format(
                    standard_example=standard_example,
                    current_script=code,
                    existing_files=existing_files,
                )
            )
        ]
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response_dict = response.model_dump()
    code_filename = response_dict["code_filename"]
    if state["memory_folder"]:
        code_filepath = Path(state["memory_folder"]) / code_filename
    else:
        code_filepath = Path(code_filename)
    if code_filepath.exists():
        code_filepath = code_filepath.with_name(
            code_filepath.stem + "_" + timestamp + code_filepath.suffix
        )
    code_filepath.write_text(code)
    return {
        "messages": [
            AIMessage(
                content="The code have been saved in the file: {code_filename}".format(
                    code_filename=code_filename,
                )
            )
        ]
    }


builder = StateGraph(LearningState)
builder.add_node("decompose", decomposing_node)
builder.add_node("associate", associating_node)
builder.add_node("memorize", memorizing_node)

builder.add_edge(START, "decompose")
builder.add_edge("decompose", "associate")
builder.add_edge("associate", "memorize")
builder.add_edge("memorize", END)
graph = builder.compile()

if __name__ == "__main__":
    # folder = Path("complete_scripts")
    # files = [f for f in folder.iterdir() if f.is_file() and f.suffix == ".py"]
    # for i, f in enumerate(files):
    #     input_state = {
    #         "messages": [],
    #         "units": [],
    #         "filepath": str(f),
    #         "memory_folder": "memory",
    #     }
    #     response = graph.invoke(input_state)
    #     print(f"{f.name} Finished. {len(files) - i - 1} left")
    pass
