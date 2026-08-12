from dotenv import load_dotenv

load_dotenv()
import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp.shared.exceptions import McpError
from mcp.types import CallToolResult, TextContent


RETRYABLE_MCP_CODES = {-32603}


class RetryMCPInterceptor:
    """
    Intercept MCP tool calls and handle transient failures.

    - Retry retryable McpError codes (e.g., -32603) with exponential backoff.
    - Return non-retryable McpError codes (e.g., -32602) immediately.
    - Retry other exceptions such as network errors, then return an error message.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def __call__(self, request, handler):
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await handler(request)

            except McpError as exc:
                last_error = exc

                print(
                    f"[MCP interceptor] {type(exc).__name__} on {request.name} "
                    f"(code {exc.error.code}, "
                    f"attempt {attempt + 1}/{self.max_retries}): {exc}"
                )

                # Do not retry non-retryable MCP errors.
                if exc.error.code not in RETRYABLE_MCP_CODES:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Tool call failed (non-retryable): {exc}",
                            )
                        ],
                        isError=False,
                    )

            except Exception as exc:
                last_error = exc

                print(
                    f"[MCP interceptor] {type(exc).__name__} on {request.name} "
                    f"(attempt {attempt + 1}/{self.max_retries}): {exc}"
                )

            # Exponential backoff: 1, 2, 4 seconds...
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2**attempt)

        print(
            f"[MCP interceptor] All {self.max_retries} retries exhausted "
            f"for {request.name}"
        )

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=(
                        f"Tool call failed after {self.max_retries} attempts: "
                        f"{last_error}"
                    ),
                )
            ],
            isError=False,
        )


client = MultiServerMCPClient(
    {
        "travel_server": {
            "transport": "streamable_http",
            "url": "https://mcp.kiwi.com",
        }
    },
    tool_interceptors=[RetryMCPInterceptor()],
)

async def get_tools_async():
    return await client.get_tools()

tools = asyncio.run(get_tools_async())

from typing import Any, Dict

from tavily import TavilyClient
from langchain.tools import tool


tavily_client = TavilyClient()

@tool
def web_search(
    query: str,
    search_number: int,
    max_search_number: int,
) -> Dict[str, Any]:
    """
    Search the web for information.

    You must track the search count by providing:
    - search_number: Current search number, starting at 1.
    - max_search_number: Maximum number of searches allowed.

    Queries must use plain text characters only.
    Do not use accented or special characters.
    For example, use 'capacite' instead of 'capacité'.
    """

    if search_number > max_search_number:
        return {
            "message": (
                "Search limit reached. Please summarize your findings "
                "and provide your final answer."
            )
        }

    try:
        return tavily_client.search(query)
    except Exception as exc:
        return {"error": str(exc)}



from pathlib import Path
from langchain_community.utilities import SQLDatabase

DB_PATH = Path(__file__).parent / "resources" / "Chinook.db"

db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")





#db = SQLDatabase.from_uri("sqlite:///resources/Chinook.db")


@tool
def query_playlist_db(query: str) -> str:
    """Query the database for playlist information."""

    try:
        return db.run(query)
    except Exception as exc:
        return f"Error querying database: {exc}"

from langchain.agents import AgentState


class WeddingState(AgentState):
    origin: str
    destination: str
    guest_count: str
    genre: str

from langchain.agents import create_agent


# Travel agent
travel_agent = create_agent(
    model="gpt-5-nano",
    tools=tools,
    system_prompt="""
You are a travel agent.

Search for flights to the desired destination wedding location.

You are not allowed to ask follow-up questions. Find the best flight
options based on the following criteria:

- Price: Lowest economy-class fare
- Duration: Shortest travel time
- Date: Time of year that you believe is best for a wedding at this location

For simplicity, search for only one one-way ticket.

You may perform multiple searches to iteratively find the best options.

You will receive only the origin and destination. It is your responsibility
to think critically and determine the best available options.

If the MCP tool fails, returns malformed output, or does not provide usable
flight results, try the tool again.

Once you have found the best options, provide the user with a shortlist.
""",
)

# Venue agent
venue_agent = create_agent(
    model="gpt-5-nano",
    tools=[web_search],
    system_prompt="""
You are a venue specialist.

Search for venues in the desired location that can accommodate the
desired number of guests.

You are not allowed to ask follow-up questions. Find the best venue
options based on the following criteria:

- Price: Lowest
- Capacity: Exact match
- Reviews: Highest

You may perform multiple searches to iteratively find the best options.

You have a suggested limit of 12 web searches. Track every
`web_search` call you make.

After 12 searches, stop searching and summarize the best options
you have found so far.
""",
)

# Playlist agent
playlist_agent = create_agent(
    model="gpt-5-nano",
    tools=[query_playlist_db],
    system_prompt="""
You are a playlist specialist.

Query the SQL database and curate the perfect wedding playlist based
on the specified genre.

Once you have created the playlist, calculate:

- Total duration
- Total cost

Each song has an associated price.

If you encounter errors when querying the database, try to fix them by
modifying your SQL query.

Do not return empty-handed. Keep trying to query the database until you
find a suitable list of songs.

The database is SQLite. Before writing any data queries, first discover
and understand the database schema.
""",
)

from langchain.tools import ToolRuntime
from langchain.messages import HumanMessage, ToolMessage
from langgraph.types import Command


@tool
async def search_flights(runtime: ToolRuntime) -> str:
    """Search for flights to the destination wedding location."""

    origin = runtime.state["origin"]
    destination = runtime.state["destination"]

    response = await travel_agent.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=f"Find flights from {origin} to {destination}"
                )
            ]
        }
    )

    return response["messages"][-1].content


@tool
def search_venues(runtime: ToolRuntime) -> str:
    """Find the best wedding venue for the location and guest capacity."""

    destination = runtime.state["destination"]
    capacity = runtime.state["guest_count"]

    query = f"Find wedding venues in {destination} for {capacity} guests"

    response = venue_agent.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ]
        }
    )

    return response["messages"][-1].content


@tool
def suggest_playlist(runtime: ToolRuntime) -> str:
    """Curate a wedding playlist based on the specified genre."""

    genre = runtime.state["genre"]

    query = f"Find {genre} tracks for wedding playlist"

    response = playlist_agent.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ]
        }
    )

    return response["messages"][-1].content


@tool
def update_state(
    origin: str,
    destination: str,
    guest_count: str,
    genre: str,
    runtime: ToolRuntime,
) -> Command:
    """
    Update the state with origin, destination, guest count, and genre.

    This tool must be called alone, without any other tool calls.
    It must complete successfully before the information is available
    to other tools.
    """

    return Command(
        update={
            "origin": origin,
            "destination": destination,
            "guest_count": guest_count,
            "genre": genre,
            "messages": [
                ToolMessage(
                    content="Successfully updated state",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )

from langchain.agents import create_agent

coordinator = create_agent(
    model="gpt-5-nano",
    tools=[
        search_flights,
        search_venues,
        suggest_playlist,
        update_state,
    ],
    state_schema=WeddingState,
    system_prompt="""
You are a wedding coordinator.

First, gather all the information you need to update the state.

Once you have all the required information, call `update_state`.

After `update_state` has completed and returned, delegate the tasks to
your specialists:

- Flights
- Venues
- Playlists

Once you receive their results, coordinate the information and create
the perfect wedding plan for the user.
""",
)




from langchain.messages import HumanMessage

async def run_wedding_planner():
    response = await coordinator.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "I'm from London and I'd like a wedding in Paris "
                        "for 100 guests, jazz genre."
                    )
                )
            ]
        },
        config={
            "tags": ["WP"],
            "recursion_limit": 40,
        },
    )
    return response



from pprint import pprint

async def main():
    response = await run_wedding_planner()
    pprint(response)
    print(response["messages"][-1].content)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())