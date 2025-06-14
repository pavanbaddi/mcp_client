import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from anthropic.types import MessageParam, ToolParam
from dotenv import load_dotenv
from typing import cast, Any
import json
import traceback

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        """"Keep context of messages"""
        self.messages: list[MessageParam] = []

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def clear_history(self):
        """Clear the conversation history"""
        self.messages = []
        print("Conversation history cleared.")

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        self.messages.append(MessageParam(role="user", content=query))
        
        if not self.session:
            raise RuntimeError("Client session is not initialized. Please connect to the server first.")

        response = await self.session.list_tools()
        available_tools = [
            ToolParam(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema
            ) for tool in response.tools
        ]

        # Initial Claude API call with full message history
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=self.messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        tool_results = []
        final_text = []
        
        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
                self.messages.append(MessageParam(role="assistant", content=content.text))
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = cast(dict[str, Any], content.input)
                
                print(f"\nCalling tool: {tool_name} with args:", tool_args)
                
                if hasattr(content, 'input') and content.input:
                    content_input = json.dumps(content.input)
                    self.messages.append(MessageParam(
                        role="assistant",
                        content=content_input
                    ))

                # tool call
                result = await self.session.call_tool(tool_name, tool_args)
                result_content = result.content[0].text if len(result.content) > 0 and result.content[0].type == 'text' else None
                tool_results.append({"call": tool_name, "result": result})
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                
                # Add tool result to message history
                self.messages.append(MessageParam(
                    role="user",
                    content=result_content or "No result returned from tool."
                ))

                # Get next response from Claude with updated history
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=self.messages,
                    tools=available_tools
                )

                first_input = response.content[0].text if len(response.content) > 0 and response.content[0].type == 'text' else None
                if first_input:
                    final_text.append(first_input)
                    # Add assistant's response to message history
                    self.messages.append(MessageParam(role="assistant", content=first_input))

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries, 'clear' to clear conversation history, or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'clear':
                    await self.clear_history()
                    continue
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError in chat_loop", e)
                traceback.print_exc()
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())