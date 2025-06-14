# MCP Client

A Python-based client implementation for the Model Context Protocol (MCP) that enables interaction with MCP servers using Claude AI.

## Features

- Connect to Python or JavaScript MCP servers
- Process queries using Claude 3 Sonnet
- Interactive chat loop interface
- Dynamic tool discovery and execution
- Async/await based implementation
- Environment variable support via dotenv

## Prerequisites

- Python 3.x
- Anthropic API key (set in `.env` file)
- MCP server implementation (Python or JavaScript)

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install mcp-python-sdk anthropic python-dotenv
```
3. Create a `.env` file and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

Run the client by providing the path to your MCP server script:

```bash
python client.py path/to/your/server_script.py

python client.py /d/mcp-servers/app2/main.py
```

Once connected, you can enter queries in the interactive chat loop. The client will:
1. Process your query using Claude
2. Discover and execute available tools from the MCP server
3. Display the results

Type 'quit' to exit the chat loop.

## Architecture

The client is built on these main components:

- `MCPClient`: Main client class that handles server connection and query processing
- `ClientSession`: Manages the MCP protocol session with the server
- `Anthropic`: Handles communication with Claude AI
- AsyncExitStack: Manages async resources and cleanup

## Error Handling

The client includes robust error handling for:
- Invalid server script paths
- Connection issues
- Query processing errors
- Tool execution failures

## License

[License information here] 

