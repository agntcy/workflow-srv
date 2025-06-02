# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import asyncio
import operator
import os
from enum import Enum
from typing import Annotated, Optional

from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field


class MsgType(Enum):
    human = "human"
    assistant = "assistant"
    ai = "ai"


class Message(BaseModel):
    type: MsgType = Field(
        ...,
        description="indicates the originator of the message, a human or an assistant",
    )
    content: str = Field(..., description="the content of the message")


class ConfigSchema(BaseModel):
    test: bool


class AgentState(BaseModel):
    messages: Annotated[Optional[list[Message]], operator.add] = []
    is_completed: Optional[bool] = None


class StatelessAgentState(BaseModel):
    messages: Optional[list[Message]] = []
    is_completed: Optional[bool] = None


class OutputState(AgentState):
    final_email: Optional[str] = Field(
        default=None,
        description="Final email produced by the mail composer, in html format",
    )


class StatelessOutputState(StatelessAgentState):
    final_email: Optional[str] = Field(
        default=None,
        description="Final email produced by the mail composer, in html format",
    )


is_stateless = os.getenv("STATELESS", "true").lower() == "true"

# Writer and subject role prompts
MARKETING_EMAIL_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """
You are a highly skilled writer and you are working for a marketing company.
Your task is to write formal and professional emails. We are building a publicity campaign and we need to send a massive number of emails to many clients.
The email must be compelling and adhere to our marketing standards.

If you need more details to complete the email, please ask me.
Once you have all the necessary information, please create the email body. The email must be engaging and persuasive. The subject that cannot exceed 5 words (no bold).
The email should be in the following format
{{separator}}
subject
body
{{separator}}
DO NOT FORGET TO ADD THE SEPARATOR BEFORE THE SUBECT AND AFTER THE EMAIL BODY!
SHOULD NEVER HAPPPEN TO HAVE THE SEPARATOR AFTER THE SUBJECT AND BEFORE THE EMAIL BODY! NEVER AFTER THE SUBJECT!
DO NOT ADD EXTRA TEXT IN THE EMAIL, LIMIT YOURSELF IN GENERATING THE EMAIL
""",
    template_format="jinja2",
)

# HELLO_MSG = ("Hello! I'm here to assist you in crafting a compelling marketing email "
#     "that resonates with your audience. To get started, could you please provide "
#     "some details about your campaign, such as the target audience, key message, "
#     "and any specific goals you have in mind?")

EMPTY_MSG_ERROR = (
    "Oops! It seems like you're trying to start a conversation with silence. ",
    "An empty message is only allowed if your email is marked complete. Otherwise, let's keep the conversation going! ",
    "Please share some details about the email you want to get.",
)

SEPARATOR = "**************"


def format_email(state):
    answer = interrupt(
        Message(
            type=MsgType.assistant,
            content="In what format would like your email to be?",
        )
    )
    state.messages = (state.messages or []) + [Message(**answer)]
    state_after_formating = generate_email(state)

    interrupt(
        Message(
            type=MsgType.assistant, content="The email is formatted, please confirm"
        )
    )

    state_after_formating = StatelessAgentState(
        **state_after_formating, is_completed=True
    )
    return final_output(state_after_formating)


def extract_mail(messages) -> str:
    for m in reversed(messages):
        splits: list[str] = []
        if isinstance(m, Message):
            if m.type == MsgType.human:
                continue
            splits = m.content.split(SEPARATOR)
        if isinstance(m, dict):
            if m.get("type", "") == "human":
                continue
            splits = m.get("content", "").split(SEPARATOR)
        if len(splits) >= 3:
            return splits[len(splits) - 2].strip()
        elif len(splits) == 2:
            return splits[1].strip()
        elif len(splits) == 1:
            return splits[0]
    return ""


def should_format_email(state: AgentState | StatelessAgentState):
    if state.is_completed and not is_stateless:
        return "format_email"
    return END


def convert_messages(messages: list) -> list[BaseMessage]:
    converted = []
    for m in messages:
        if isinstance(m, Message):
            mdict = m.model_dump()
        else:
            mdict = m
        if mdict["type"] == "human":
            converted.append(HumanMessage(content=mdict["content"]))
        else:
            converted.append(AIMessage(content=mdict["content"]))

    return converted


# Define mail_agent function
def email_agent(
    state: AgentState | StatelessAgentState,
) -> OutputState | AgentState | StatelessOutputState | StatelessAgentState:
    """This agent is a skilled writer for a marketing company, creating formal and professional emails for publicity campaigns.
    It interacts with users to gather the necessary details.
    Once the user approves by sending "is_completed": true, the agent outputs the finalized email in "final_email".
    """
    # Check subsequent messages and handle completion
    return final_output(state) if state.is_completed else generate_email(state)


def final_output(
    state: AgentState | StatelessAgentState,
) -> OutputState | AgentState | StatelessOutputState | StatelessAgentState:
    final_mail = extract_mail(state.messages)

    output_state: OutputState = OutputState(
        messages=state.messages,
        is_completed=state.is_completed,
        final_email=final_mail,
    )
    return output_state


def generate_email(
    state: AgentState | StatelessAgentState,
) -> OutputState | AgentState | StatelessOutputState | StatelessAgentState:
    ai_message = Message(
        type=MsgType.ai, content="this is a placeholder for the AI response"
    )

    if is_stateless:
        return {"messages": state.messages + [ai_message]}

    else:
        return {"messages": [ai_message]}


async def main():
    if is_stateless:
        graph_builder = StateGraph(StatelessAgentState, output=StatelessOutputState)
    else:
        graph_builder = StateGraph(AgentState, output=OutputState)

    graph_builder.add_node("email_agent", email_agent)
    graph_builder.add_node("format_email", format_email)

    graph_builder.add_edge(START, "email_agent")
    # This node will only be added in stateful mode since langgraph requires checkpointer if any node should interrupt
    graph_builder.add_conditional_edges("email_agent", should_format_email)
    graph_builder.add_edge("format_email", END)
    graph_builder.add_edge("email_agent", END)

    if is_stateless:
        print("mailcomposer - running in stateless mode")
        _ = graph_builder.compile()
    else:
        print("mailcomposer - running in stateful mode")
        checkpointer = InMemorySaver()
        _ = graph_builder.compile(checkpointer=checkpointer)


def CreateLanggraphWorkflow():
    graph_builder = StateGraph(AgentState, output=OutputState)
    graph_builder.add_node("email_agent", email_agent)
    graph_builder.add_node("format_email", format_email)

    graph_builder.add_edge(START, "email_agent")
    # This node will only be added in stateful mode since langgraph requires checkpointer if any node should interrupt
    graph_builder.add_conditional_edges("email_agent", should_format_email)
    graph_builder.add_edge("format_email", END)
    graph_builder.add_edge("email_agent", END)

    return graph_builder


def GetLanggraphWorkflow():
    w = CreateLanggraphWorkflow()
    print("mailcomposer - running in stateful mode")
    checkpointer = InMemorySaver()
    graph = w.compile(checkpointer=checkpointer)
    return graph


if __name__ == "__main__":
    asyncio.run(main())
