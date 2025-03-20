import os
from typing import Annotated
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import AzureChatOpenAI
from typing_extensions import TypedDict
from langchain.prompts import PromptTemplate


# Initialize the Azure OpenAI model
api_key = os.getenv("AZURE_OPENAI_API_KEY")
if not api_key:
    raise ValueError("AZURE_OPENAI_API_KEY must be set as an environment variable.")

llm = AzureChatOpenAI(
    api_key=api_key,
    azure_endpoint="https://smith-project-agents.openai.azure.com",
    model_name="gpt-4o",
    openai_api_type="azure_openai",
    api_version="2024-07-01-preview",
    temperature=0,
    max_retries=10,
    seed=42
)

# Writer and subject role prompts
MARKETING_EMAIL_PROMPT_TEMPLATE = PromptTemplate.from_template(
"""
You are a highly skilled writer and you are working for a marketing company.
Your task is to write formal and professional emails. We are building a publicity campaign and we need to send a massive number of emails to many clients.
The email must be compelling and adhere to our marketing standards.

If you need more details to complete the email, please ask me.
Once you have all the necessary information, please create the email body. The email must be engaging and persuasive. The subject that cannot exceed 5 words (no bold).
Mark the beginning and the end of the email with the separator {{separator}}.
DO NOT FORGET TO ADD THE SEPARATOR BEFORE THE SUBECT AND AFTER THE EMAIL BODY!!
""",
template_format="jinja2")

# HELLO_MSG = ("Hello! I'm here to assist you in crafting a compelling marketing email "
#     "that resonates with your audience. To get started, could you please provide "
#     "some details about your campaign, such as the target audience, key message, "
#     "and any specific goals you have in mind?")

EMPTY_MSG_ERROR = ("Oops! It seems like you're trying to start a conversation with silence. ",
    "An empty message is only allowed if your email is marked complete. Otherwise, let's keep the conversation going! ",
    "Please share some details about the email you want to get.")

SEPARATOR = "**************"

# Define the state structures
class AgentState(TypedDict, total=False):
    messages: list[BaseMessage]
    is_completed: bool

class OutputState(AgentState):
    final_email: str

def extract_mail(messages):
    for m in reversed(messages):
        if m.type == "human": continue
        splits = m.content.split(SEPARATOR)
        if len(splits) > 1:
            return splits[1]

    return ""

# Define mail_agent function
def email_agent(state: AgentState):
    """This agent is a skilled writer for a marketing company, creating formal and professional emails for publicity campaigns. 
    It interacts with users to gather the necessary details. 
    Once the user approves by sending "is_completed": true, the agent outputs the finalized email in "final_email"."""

    # Check if the first message is empty
    #if not state.get("messages", []) or state["messages"][-1].content == EMPTY_MSG_ERROR:
    #    state["is_completed"] = False
    #    return {"messages": [AIMessage(
    #        content=EMPTY_MSG_ERROR
    #        )]}

    # Check subsequent messages and handle completion
    if state.get("is_completed", False):
        final_mail = extract_mail(state["messages"])
        state["final_email"] = final_mail
        return state
        #return {"messages": [AIMessage(content=final_mail)]}

    # Generate the email
    llm_messages = [
        HumanMessage(content = MARKETING_EMAIL_PROMPT_TEMPLATE.format(separator=SEPARATOR)),
    ] + state["messages"]


    state["messages"] = state["messages"] + [AIMessage(content=llm.invoke(llm_messages).content)]
    return state

# Create the graph and add the agent node
graph_builder = StateGraph(AgentState, output=OutputState)
graph_builder.add_node("email_agent", email_agent)

graph_builder.add_edge(START, "email_agent")
graph_builder.add_edge("email_agent", END)

# Compile the graph
graph = graph_builder.compile()
