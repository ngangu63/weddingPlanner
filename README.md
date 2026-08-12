# Wedding Planner AI Agent

A multi-agent wedding planning application built with **Python**, **LangChain**, **LangGraph agent state**, **MCP (Model Context Protocol)**, **Tavily Web Search**, and a **SQLite** database.

The application uses a coordinator agent to collect wedding requirements and delegate specialized tasks to three agents:

- ✈️ **Travel Agent** — searches for flight options using an MCP travel server.
- 🏛️ **Venue Agent** — searches the web for suitable wedding venues.
- 🎵 **Playlist Agent** — queries a SQLite music database and creates a wedding playlist.
- 🤵 **Wedding Coordinator** — orchestrates the specialists and produces the final wedding plan.

## Architecture

```text
                         ┌──────────────────────┐
                         │        User          │
                         │ Wedding Requirements │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Wedding Coordinator │
                         │      Agent           │
                         └──────────┬───────────┘
                                    │
                         update_state()
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
          ┌──────────────┐  ┌──────────────┐  ┌────────────────┐
          │ Travel Agent │  │ Venue Agent  │  │ Playlist Agent │
          └──────┬───────┘  └──────┬───────┘  └───────┬────────┘
                 │                 │                  │
                 ▼                 ▼                  ▼
          MCP Travel Server   Tavily Web Search   SQLite/Chinook
                 │                 │                  │
                 └─────────────────┼──────────────────┘
                                   ▼
                         ┌──────────────────────┐
                         │ Final Wedding Plan   │
                         └──────────────────────┘
```

## Features

### Multi-Agent Orchestration

The coordinator agent manages the overall workflow and delegates specialized work to independent agents.

The coordinator is configured with:

- `search_flights`
- `search_venues`
- `suggest_playlist`
- `update_state`

The implementation uses `create_agent()` and a custom `WeddingState` schema. fileciteturn0file0L164-L180

### Shared Wedding State

The application maintains the following state:

```python
class WeddingState(AgentState):
    origin: str
    destination: str
    guest_count: str
    genre: str
```

This allows the coordinator and specialist tools to share the user's wedding requirements. fileciteturn0file0L164-L171

### MCP Travel Integration

The travel agent uses `MultiServerMCPClient` to connect to the configured travel MCP server:

```python
client = MultiServerMCPClient(
    {
        "travel_server": {
            "transport": "streamable_http",
            "url": "https://mcp.kiwi.com",
        }
    },
    tool_interceptors=[RetryMCPInterceptor()],
)
```

The MCP tools are loaded asynchronously with `client.get_tools()`. fileciteturn0file0L85-L98

### MCP Retry Handling

A custom `RetryMCPInterceptor` handles transient MCP failures.

It:

- Retries retryable MCP errors.
- Immediately returns non-retryable MCP errors.
- Retries unexpected exceptions such as network failures.
- Uses exponential backoff: `1`, `2`, `4` seconds.
- Stops after the configured maximum number of retries.

The default retry count is three attempts. fileciteturn0file0L14-L24

### Web Search

The venue agent uses a `web_search` LangChain tool backed by Tavily.

The tool tracks the number of searches and supports a maximum-search limit:

```python
web_search(
    query,
    search_number,
    max_search_number,
)
```

The venue agent is instructed to stop after 12 searches and summarize the best options found. fileciteturn0file0L106-L135

### SQLite Playlist Database

The playlist agent uses a SQLite database:

```text
resources/Chinook.db
```

The database is loaded relative to the Python source file:

```python
DB_PATH = Path(__file__).parent / "resources" / "Chinook.db"
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
```

The `query_playlist_db` tool allows the playlist agent to execute SQL queries against the database. fileciteturn0file0L141-L160

## Agent Responsibilities

### 1. Wedding Coordinator

The coordinator:

1. Extracts the wedding requirements.
2. Updates the shared `WeddingState`.
3. Delegates flight, venue, and playlist tasks.
4. Collects specialist responses.
5. Combines the results into a final wedding plan.

The coordinator explicitly requires `update_state` to complete before other tools use the wedding information. fileciteturn0file0L326-L350

### 2. Travel Agent

The travel agent receives the origin and destination and searches for flight options.

Its selection criteria are:

- Lowest economy-class fare.
- Shortest travel time.
- Appropriate time of year for a wedding at the destination.
- One-way ticket for simplicity.

It can retry the MCP tool when results are unavailable or malformed. fileciteturn0file0L176-L203

### 3. Venue Agent

The venue agent searches for wedding venues based on:

- Destination.
- Number of guests.
- Lowest price.
- Exact capacity match.
- Highest reviews.

It can perform multiple searches and has a suggested maximum of 12 web searches. fileciteturn0file0L206-L230

### 4. Playlist Agent

The playlist agent queries the SQLite database and creates a wedding playlist based on the requested genre.

It calculates:

- Total playlist duration.
- Total playlist cost.

Before constructing data queries, the agent is instructed to discover and understand the database schema. fileciteturn0file0L233-L259

## Project Structure

A recommended project structure is:

```text
project/
├── wedding_planner.py
├── .env
├── .gitignore
├── README.md
└── resources/
    └── Chinook.db
```

The SQLite database is expected under the `resources` directory relative to the Python source file. fileciteturn0file0L141-L146

## Requirements

The application requires Python and the following major packages:

- `langchain`
- `langchain-mcp-adapters`
- `langchain-community`
- `langgraph`
- `mcp`
- `tavily-python`
- `python-dotenv`

The application also requires access to:

- An OpenAI-compatible model configured as `gpt-5-nano`.
- The configured MCP travel server.
- Tavily Web Search.
- The local SQLite database.

## Environment Variables

Create a `.env` file in the project root.

Example:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Do not commit `.env` or API keys to source control.

Recommended `.gitignore` entries:

```gitignore
.env
__pycache__/
*.pyc
.venv/
```

## Installation

### 1. Create a virtual environment

Using standard Python:

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

Install the required packages using your preferred package manager.

For example:

```bash
pip install langchain langchain-mcp-adapters langchain-community langgraph mcp tavily-python python-dotenv
```

If the project uses `uv`, install the dependencies through the project's `pyproject.toml`.

## Database Setup

Make sure the SQLite database exists at:

```text
resources/Chinook.db
```

The application builds the database path dynamically:

```python
DB_PATH = Path(__file__).parent / "resources" / "Chinook.db"
```

This avoids depending on the current working directory when the application is started. fileciteturn0file0L141-L146

## Running the Application

The application exposes an asynchronous entry point:

```python
async def run_wedding_planner():
    response = await coordinator.ainvoke(...)
    return response
```

The script starts the application through:

```python
if __name__ == "__main__":
    asyncio.run(main())
```

fileciteturn0file0L389-L422

Run it with:

```bash
python wedding_planner.py
```

If the project is organized as a Python package, it can instead be run with:

```bash
python -m your_package.wedding_planner
```

## Example Request

The included example asks the coordinator to plan:

```text
I'm from London and I'd like a wedding in Paris
for 100 guests, jazz genre.
```

fileciteturn0file0L391-L408

The coordinator extracts:

```text
Origin:       London
Destination:  Paris
Guests:       100
Genre:        jazz
```

It then delegates the work to the specialist agents.

## Workflow

The overall execution flow is:

```text
1. User provides wedding requirements
             │
             ▼
2. Coordinator extracts:
   - origin
   - destination
   - guest count
   - genre
             │
             ▼
3. update_state()
             │
             ▼
4. Search flights
             │
             ├── Travel Agent
             └── MCP Travel Server
             │
             ▼
5. Search venues
             │
             ├── Venue Agent
             └── Tavily
             │
             ▼
6. Build playlist
             │
             ├── Playlist Agent
             └── SQLite
             │
             ▼
7. Coordinator combines results
             │
             ▼
8. Final wedding plan
```

## Error Handling

### MCP Errors

MCP errors are inspected by error code.

The application currently treats:

```python
RETRYABLE_MCP_CODES = {-32603}
```

as retryable. Other MCP errors, such as `-32602`, are returned without retrying. fileciteturn0file0L11-L20

### Network and Unexpected Errors

Unexpected exceptions are also retried using exponential backoff.

After all attempts fail, the interceptor returns a `CallToolResult` containing the error message. fileciteturn0file0L54-L81

### Database Errors

The playlist database tool catches database exceptions and returns an error message:

```python
try:
    return db.run(query)
except Exception as exc:
    return f"Error querying database: {exc}"
```

fileciteturn0file0L156-L162

## LangChain Agent State

The project demonstrates how custom application state can extend `AgentState`.

```python
class WeddingState(AgentState):
    origin: str
    destination: str
    guest_count: str
    genre: str
```

The coordinator registers this state through:

```python
coordinator = create_agent(
    ...
    state_schema=WeddingState,
)
```

fileciteturn0file0L356-L366

## Tool Runtime

The specialist tools access shared state through `ToolRuntime`.

For example, the flight tool reads:

```python
origin = runtime.state["origin"]
destination = runtime.state["destination"]
```

and then invokes the travel agent asynchronously. fileciteturn0file0L261-L283

The venue and playlist tools similarly retrieve destination, guest count, and genre from the runtime state. fileciteturn0file0L287-L322

## Recursion Limit and Tags

The example invocation configures:

```python
config={
    "tags": ["WP"],
    "recursion_limit": 40,
}
```

This provides a tag for tracing/identification and limits the agent execution recursion depth. fileciteturn0file0L403-L405

## Troubleshooting

### `Chinook.db` Not Found

Verify that the database exists here:

```text
resources/Chinook.db
```

The application resolves the path relative to the Python file rather than the shell's current directory.

### MCP Travel Tool Failure

Check:

- Internet connectivity.
- MCP server availability.
- MCP client package versions.
- API/server compatibility.
- Error messages from `RetryMCPInterceptor`.

The interceptor automatically retries transient failures up to three times by default. fileciteturn0file0L23-L24

### Tavily Search Failure

Check that `TAVILY_API_KEY` is configured and that the Tavily client can access the service.

The web-search tool catches exceptions and returns them as an error object. fileciteturn0file0L126-L137

### Empty Playlist Results

The playlist agent is instructed to:

1. Discover the database schema.
2. Build an appropriate SQL query.
3. Modify the query if an error occurs.
4. Continue querying until it finds a suitable playlist.

fileciteturn0file0L250-L259

## Design Patterns Demonstrated

This project is a useful example of several modern agent-development patterns:

- **Multi-agent orchestration**
- **Specialist agents**
- **Shared typed agent state**
- **Tool-based delegation**
- **MCP integration**
- **MCP retry middleware/interceptors**
- **Web search tools**
- **SQL database tools**
- **Asynchronous agent execution**
- **Agent runtime context**
- **Error handling and retries**
- **Agent recursion limits**

## Future Improvements

Potential enhancements include:

1. Add explicit input validation for guest count and destination.
2. Add wedding date and budget to `WeddingState`.
3. Add currency conversion for international weddings.
4. Add hotel and transportation agents.
5. Add restaurant/catering recommendations.
6. Add a weather agent.
7. Persist completed wedding plans.
8. Add LangSmith tracing and evaluation.
9. Add unit and integration tests.
10. Add structured output schemas for specialist agents.
11. Add human approval before finalizing recommendations.
12. Containerize the application with Docker.
13. Deploy the coordinator and MCP services to AWS.
14. Add authentication and authorization for production deployments.

## Technologies

| Technology | Purpose |
|---|---|
| Python | Application language |
| LangChain | Agent and tool framework |
| LangGraph | Agent state/orchestration infrastructure |
| MCP | External tool/server integration |
| OpenAI | LLM |
| Tavily | Web search |
| SQLite | Playlist data |
| Chinook | Sample music database |
| python-dotenv | Environment configuration |

## License

Add the project's license information here.

## Author

**Remy Miantezila**
