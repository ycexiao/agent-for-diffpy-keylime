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
from langchain_core.documents import Document
import json

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


def digest_code(folder_path, save_name="code_vectorstore"):
    global embeddings
    folder = Path(folder_path)
    docs = []
    for f in folder.iterdir():
        doc_content = f.read_text()
        chunks = doc_content.split("\n\n# ---\n\n")
        for chunk in chunks:
            docs.append(Document(page_content=chunk))
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(save_name)


def digest_skeleton(folder_path, save_name="skeleton_vectorstore"):
    global embeddings
    folder = Path(folder_path)
    docs = []
    for f in folder.iterdir():
        doc_content = f.read_text()
        chunks = doc_content.split("\n\n# ---\n\n")
        for chunk in chunks:
            lines = chunk.splitlines()
            lines = [l for l in lines if l.strip().startswith("#")]
            chunk = "\n".join(lines)
            docs.append(Document(page_content=chunk))
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(save_name)


def digest_docstring(folder_path, save_name="docstring_vectorstore"):
    global embeddings
    folder = Path(folder_path)
    docs = []
    for f in folder.iterdir():
        doc_content = f.read_text()
        items = json.loads(doc_content)
        for cls_or_func in items:
            page_content = f"{cls_or_func['kind']} : {cls_or_func['name']}\n{cls_or_func['content']}"
            docs.append(Document(page_content=page_content))
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(save_name)


if __name__ == "__main__":
    # digest_code("code")
    # digest_skeleton("skeleton")

    # digest_docstring("doc_summaries")
    # docstring_vectorstore = FAISS.load_local(
    #     "docstring_vectorstore",
    #     allow_dangerous_deserialization=True,
    #     embeddings=embeddings,
    # )
    # docs = docstring_vectorstore.similarity_search(
    #     "diffpy.srfit.fitbase.FitRecipe", k=3
    # )
    # for doc in docs:
    #     print(doc.page_content)
    #     print("-----")
    pass
