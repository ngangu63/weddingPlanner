from dotenv import load_dotenv

load_dotenv()


# Creating subagents

from langchain.tools import tool


@tool
def square_root(x: float) -> float:
    """Calculate the square root of a number."""
    return x ** 0.5


@tool
def square(x: float) -> float:
    """Calculate the square of a number."""
    return x ** 2

from langchain.agents import create_agent


# Create subagents

subagent_1 = create_agent(
    model="gpt-5-nano",
    tools=[square_root],
)

subagent_2 = create_agent(
    model="gpt-5-nano",
    tools=[square],
)

from langchain.messages import HumanMessage
from langchain.agents import create_agent
from langchain.tools import tool


# Calling subagents

@tool
def call_subagent_1(x: float) -> float:
    """Call subagent 1 to calculate the square root of a number."""
    response = subagent_1.invoke({
        "messages": [
            HumanMessage(content=f"Calculate the square root of {x}")
        ]
    })

    return response["messages"][-1].content


@tool
def call_subagent_2(x: float) -> float:
    """Call subagent 2 to calculate the square of a number."""
    response = subagent_2.invoke({
        "messages": [
            HumanMessage(content=f"Calculate the square of {x}")
        ]
    })

    return response["messages"][-1].content


# Creating the main agent

main_agent = create_agent(
    model="gpt-5-nano",
    tools=[call_subagent_1, call_subagent_2],
    system_prompt=(
        "You are a helpful assistant who can call subagents "
        "to calculate the square root or square of a number."
    ),
)
question1 = "What is the square root of 100?"

response = main_agent.invoke({
    "messages": [HumanMessage(content=question1)]
})

from pprint import pprint

#pprint(response["messages"][-1].content)


question2 = "What is the square of 9?"

response3 = main_agent.invoke({
    "messages": [HumanMessage(content=question2)]
})

from pprint import pprint

pprint(response3["messages"][-1].content)