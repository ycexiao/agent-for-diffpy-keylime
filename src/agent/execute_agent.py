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


@tool
def execute_and_analyze_node(code_content):
    """
    Execute the code content and return the outcome, including the stdout, stderr and error if any.

    Parameters
    ----------
    code_content : str
        The code content to be executed

    Returns
    ------
    dict
        The outcome of the code execution, including stdout, stderr, and error if any.
    """

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exec(code_content, {})
        traceback_error = None
    except Exception:
        traceback_error = traceback.format_exc()
    outcome = f"""
stdout: {stdout_buffer.getvalue()},
stdout: {stdout_buffer.getvalue()},
stderr: {stderr_buffer.getvalue()},
error: {traceback_error},
"""
    return outcome


def code_agent(state):
    system_prompt = """
You are a hepful assistant for executing and analysing the feedback of the code.

If not specified, you are only supposed to execute the code once, and return the 
analysis immediately.

If specified, you can asscept the feedback and fix the code accordingly under
a certain number of iterations until the code can be executed without error.
The default number of iterations is 3 if not specified by the user.
"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    llm_with_tool = llm.bind_tools(tools=[execute_and_analyze_node])
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tool.invoke(messages)
    yield Command(update={"messages": [response]})


run_tool = ToolNode(tools=[execute_and_analyze_node])

builder = StateGraph(MessagesState)
builder.add_node("code_agent", code_agent)
builder.add_node("run_tool", run_tool)
builder.add_conditional_edges(
    "code_agent", tools_condition, {"tools": "run_tool", END: END}
)
builder.add_edge("run_tool", "code_agent")
builder.add_edge(START, "code_agent")
graph = builder.compile()

if __name__ == "__main__":
    # input_state = [
    #     HumanMessage(
    #         content="Here is the code snippet: ```python\nprint(su(range(10)))\n```"
    #     )
    # ]
    # response = graph.invoke({"messages": input_state})
    # for msg in response["messages"]:
    #     msg.pretty_print()
    pass
