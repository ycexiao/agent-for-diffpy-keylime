from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
)
from typing import TypedDict, List, Literal
from pydantic import BaseModel, Field
from langgraph.types import Command
from langgraph.graph import MessagesState
from agent.code_agent import graph as code_subgraph
from agent.execute_agent import graph as execute_subgraph


def supervisor_node(state):
    system_prompt = """
    You are a helpful assistant for dispatching task to different agents, and
    chat with users.

    You can dispatch task to two agents: code_agent and execute_agent. 
    
    The code_agent is responsible for generating code snippets writing scripts
    to perform PDF(pair distribution function) refinement based on user queries
    
    The execute_agent is responsible for executing the code snippets and 
    analyzing the outcome.

    You shouldn't add any supplementary explanation in the message, 
    and just directly give the message to user or other agent.

    You MUST NOT MODIFY the user query, or wasting tokens to add any explanation
    or plans.
    """

    class OutputSchema(BaseModel):
        message: str = Field(
            description="The message to be sent to user or other agent"
        )
        agent: Literal["code_agent", "execute_agent", "END"] = Field(
            description="The agent to handle the task, either code_agent, execute_agent, or END"
        )

    llm = ChatOpenAI(model="gpt-5", temperature=0.2)
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    structured_llm = llm.with_structured_output(OutputSchema)
    response = structured_llm.invoke(messages)
    response = response.model_dump()
    yield Command(
        update={"messages": [AIMessage(content=response["message"])]},
        goto=f"{response['agent']}.entry_point",
    )


builder = StateGraph(MessagesState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("code_agent.entry_point", code_subgraph)
builder.add_node("execute_agent.entry_point", execute_subgraph)
builder.set_entry_point("supervisor")
graph = builder.compile()

if __name__ == "__main__":
    input_state = {
        "messages": [
            HumanMessage(
                content="Execute and analysis the following code 'print(list(range(10)))'"
            )
        ]
    }

    for update in graph.stream(
        input_state, subgraphs=True, stream_mode="updates"
    ):
        node_path, states = update
        # Iterate over all subgraph states in this update
        for state_name, state_dict in states.items():
            if "messages" in state_dict:
                for msg in state_dict["messages"]:
                    for line in msg.content.splitlines():
                        print(line, flush=True)
