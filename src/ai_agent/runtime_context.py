from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from langchain.agents import create_agent
from langchain.messages import HumanMessage 

from dataclasses import dataclass
@dataclass
class ColourContext:
    """A class to hold colour context information."""
    favourite_colour: str ="blue"
    least_favourite_colour: str = "yellow"


agent = create_agent(
    model="gpt-5-nano",  # Specify the model to use
    context_schema=ColourContext,  # Use the ColourContext dataclass for context
)

response = agent.invoke (
    {"messages": [HumanMessage(content="What is your favourite colour?")]},
    context=ColourContext()
)
from pprint import pprint
#pprint(response)


from langchain.tools import tool, ToolRuntime
@tool
def get_favourite_colour(runtime: ToolRuntime)-> str:
    """ Get the favourite colour of the user """
    return runtime.context.favourite_colour

 
@tool
def get_least_favourite_colour(runtime: ToolRuntime)-> str:
    """ Get the least favourite colour of the user """
    return runtime.context.least_favourite_colour

agent = create_agent(
    model="gpt-5-nano",  # Specify the model to use
    tools=[get_favourite_colour, get_least_favourite_colour],  # Register the tools
    context_schema=ColourContext,  # Use the ColourContext dataclass for context
)
response = agent.invoke (
    {"messages": [HumanMessage(content="What is your favourite colour?")]},
    context=ColourContext()
)

#pprint(response)

response = agent.invoke (
    {"messages": [HumanMessage(content="What is your favourite colour?")]},
    context=ColourContext(favourite_colour="green")
)
pprint(response)