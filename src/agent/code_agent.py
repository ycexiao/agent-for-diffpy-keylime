from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path
import traceback

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

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from langgraph.prebuilt import tools_condition
import ast

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

skeleton_folder = Path(__file__).parents[2] / "skeleton_vectorstore"
code_folder = Path(__file__).parents[2] / "code_vectorstore"

skeleton_vectorstore = FAISS.load_local(
    str(skeleton_folder), embeddings, allow_dangerous_deserialization=True
)
code_vectorstore = FAISS.load_local(
    str(code_folder), embeddings, allow_dangerous_deserialization=True
)


def generate_skeleton_node(state):
    system_prompt = """
You are a helpful assistant for generating queries to fetch guidelines to 
write code for structure analysis of material with experiment dataset.

User might ask to implement the same functionality in different ways, you need
to identify them, and make it clear and straightforward to run simularity search
in the vectorstore to get the correct guidelines.

The support functionalities include:
1. write a diffpy.srfit script to fit one experiment dataset with one phase, considering only the scaling factor, and refines all the parameters available (e.g. qdamp, qbroad, spacegroupparams, ...)
2. write a diffpy.srfit script to fit one experiment dataset with two phases
3. also consider the spherical nanoparticle effect in the fitting
4. insert atoms in specific sites while pretain the total occupancy number
5. constrain usio of atoms in the structural model during refinement

Only return one single query with no other words. If user asked something outside the scope, explain the supported functionalities.
"""
    global skeleton_vectorstore

    class OutputSchema(BaseModel):
        response: str = Field(
            description="The response message containing the query to fetch the skeleton, or explaination about why the question is out of scope, and what are the supported functionalities."
        )
        inside_scope: bool = Field(
            description="Whether the user question is within the scope that the skeleton vectorstore can support."
        )

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    structured_llm = llm.with_structured_output(OutputSchema)
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = structured_llm.invoke(messages).model_dump()
    response_message = response["response"]
    inside_scope = response["inside_scope"]
    if not inside_scope:
        yield Command(
            update={"messages": [AIMessage(content=response_message)]},
            goto="END",
        )
    docs = skeleton_vectorstore.similarity_search(response_message, k=1)
    yield Command(
        update={
            "messages": [
                AIMessage(content=f"Skeleton below: {docs[0].page_content}")
            ]
        }
    )


def compose_code_node(state):
    system_prompt = """
You are a helpful assistant that can
1. generate queries based on the provided skeleton about how to complete a task. You should generate one query per each step in the skeleton.
2. use the tool `retrieve_snippets` to fetch code snippets according to the queries
3. compose the code snippets together as a complete code implementation to solve the problem. 
4. You can also modify the code snippets to make them work together, but you should not change the core logic of the code snippets.

Special processes are needed during the composition:

* User inputs
In the retrieved code snippets, there might be variables taht are referenced
without being initiated.

If user provide the value in their prompt, initialize these variables in the 
begining section of the completed script.

If user didn't provide the value, remove the component involving these using
these values. Provide dummy values for these variables if they are necessary 
for the code to run. These variables should be initialized in the beginning section of the completed script.

The last message should only be python script that can be directly run to 
solve the problem. Don't include any other words or explanation. Don't include
markdown format, e.g. ```python and ```  in the response. Only return the code 
content.
"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    llm_with_tool = llm.bind_tools(tools=[retrieve_snippets])
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tool.invoke(messages)
    yield Command(update={"messages": response})


def finalze_code_node(state):
    system_prompt = """
You are a helpful assistant for revising the python code and make sure the 
syntax is correct. You can use the tool `syntax_check` get the feedback.

By default, you can try max 3 times to get the correct script
"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    llm_with_tool = llm.bind_tools(tools=[syntax_check])
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tool.invoke(messages)
    yield Command(update={"messages": response})


@tool
def syntax_check(code_content):
    """
    Check whether the code content has syntax error. If there is syntax error, return the error message. If there is no syntax error, return "No syntax error".

    Parameters
    ----------
    code_content : str
        The code content to be checked

    Returns
    ------
    str
        The outcome of the syntax check, either the error message or "No syntax error"
    """
    try:
        ast.parse(code_content)
        return "No syntax error"
    except SyntaxError as e:
        return f"Syntax error: {str(e)}"


@tool
def retrieve_snippets(query: str) -> str:
    """
    This function fetches the corresponding code implementation based on the
    query text

    Parameters
    ----------
    query : text
        The query used to search through the vectorstore

    Returns
    ------
    str
        The code snippet
    """
    docs = code_vectorstore.similarity_search(query, k=1)
    return docs[0].page_content


@tool
def write_file(filename: str, content: str):
    """
    Write the content to a file with the given filename.

    Parameters
    ----------
    filename : str
        The name of the file to write to
    content : str
        The content to write to the file

    Returns
    ------
    str
        The outcom    messages = [SystemMessage(content=system_prompt)] + state["messages"]e of the file writing operation.
    """
    file_path = Path(filename)
    if file_path.exists():
        file_path = file_path.with_name(
            f"{file_path.stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_path.suffix}"
        )
    file_path.write_text(content)
    return f"File written successfully to {str(file_path)}"


syntax_check_tool = ToolNode(tools=[syntax_check])
fetch_code_tool = ToolNode(tools=[retrieve_snippets])
builder = StateGraph(MessagesState)
builder.add_node("skeleton", generate_skeleton_node)
builder.add_node("compose", compose_code_node)
builder.add_node("code_tool", fetch_code_tool)

builder.add_edge("skeleton", "compose")
builder.add_conditional_edges(
    "compose", tools_condition, {"tools": "code_tool", END: END}
)
builder.add_edge("code_tool", "compose")
builder.add_edge(START, "skeleton")

graph = builder.compile()

if __name__ == "__main__":
    outcome = graph.invoke(
        {
            "messages": "I have a Ni.cif and Ni.gr file, and I want to do PDF refinement."
        }
    )
    for msg in outcome["messages"]:
        msg.pretty_print()
