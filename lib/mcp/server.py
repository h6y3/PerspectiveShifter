"""
MCP Server for PerspectiveShifter - Claude Desktop Integration

This module implements the Model Context Protocol server that enables
Claude Desktop to connect and use PerspectiveShifter tools.

STRANGLER PATTERN STATUS: Phase 3 - MCP Integration
- Uses new WisdomService via MCP tools
- Provides Claude Desktop integration
- Maintains existing rate limiting and cost tracking
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from lib.mcp.tools import get_available_tools, execute_mcp_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """
    Model Context Protocol server for PerspectiveShifter.
    
    This server enables Claude Desktop to discover and use PerspectiveShifter
    tools for wisdom quote generation.
    """
    
    def __init__(self):
        self.name = "perspectiveshifter"
        self.version = "1.0.0"
        self.description = "Generate personalized wisdom quotes and shareable images"
        self.tools = get_available_tools()
        self.logger = logger
        
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information for MCP handshake"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "protocol_version": "2024-11-05",
            "capabilities": {
                "tools": {
                    "list_changed": False
                },
                "resources": {
                    "subscribe": False,
                    "list_changed": False
                },
                "prompts": {
                    "list_changed": False
                }
            }
        }
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools for Claude Desktop"""
        return {
            "tools": self.tools
        }
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call from Claude Desktop.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            MCP tool response
        """
        self.logger.info(f"MCP tool call: {tool_name} with args: {arguments}")
        
        try:
            # Execute the tool
            result = execute_mcp_tool(tool_name, arguments)
            
            # Log successful execution
            self.logger.info(f"MCP tool {tool_name} executed successfully")
            
            # Return MCP-formatted response
            return {
                "content": [result],
                "isError": False
            }
            
        except Exception as e:
            self.logger.error(f"MCP tool execution error: {str(e)}")
            
            # Return error response
            error_result = {
                "type": "text",
                "text": f"Tool execution failed: {str(e)}",
                "metadata": {
                    "error": True,
                    "message": str(e),
                    "tool": tool_name,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            return {
                "content": [error_result],
                "isError": True
            }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP requests.
        
        Args:
            request: MCP request message
            
        Returns:
            MCP response message
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            self.logger.info(f"MCP request: {method}")
            
            # Handle different MCP methods
            if method == "initialize":
                response_data = self.get_server_info()
            elif method == "tools/list":
                response_data = self.list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response_data = self.call_tool(tool_name, arguments)
            else:
                self.logger.warning(f"Unknown MCP method: {method}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Return successful response
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response_data
            }
            
        except Exception as e:
            self.logger.error(f"MCP request handling error: {str(e)}")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }


# Global MCP server instance
mcp_server = MCPServer()


def create_mcp_config() -> Dict[str, Any]:
    """
    Create MCP configuration for Claude Desktop.
    
    This configuration should be added to Claude Desktop's MCP settings.
    """
    return {
        "mcpServers": {
            "perspectiveshifter": {
                "command": "python",
                "args": ["-m", "lib.mcp.server"],
                "cwd": "/path/to/perspectiveshifter",
                "env": {
                    "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                    "DATABASE_URL": "${DATABASE_URL}",
                    "API_DAILY_BUDGET_USD": "1.00"
                }
            }
        }
    }


def create_standalone_mcp_config() -> Dict[str, Any]:
    """
    Create standalone MCP configuration that connects to deployed API.
    
    This configuration allows Claude Desktop to use the deployed Vercel API
    without requiring local server setup.
    """
    return {
        "mcpServers": {
            "perspectiveshifter": {
                "command": "python",
                "args": ["-c", """
import json
import requests
import sys

class PerspectiveShifterMCP:
    def __init__(self):
        self.base_url = "https://theperspectiveshift.vercel.app/api/v1"
    
    def handle_request(self, request):
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "name": "perspectiveshifter",
                "version": "1.0.0",
                "protocol_version": "2024-11-05",
                "capabilities": {"tools": {"list_changed": False}}
            }
        elif method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "generate_wisdom_quote",
                        "description": "Generate personalized wisdom quotes",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_input": {"type": "string", "description": "User situation or feeling"},
                                "style": {"type": "string", "enum": ["inspirational", "practical", "philosophical", "humorous"]}
                            },
                            "required": ["user_input"]
                        }
                    }
                ]
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            
            if tool_name == "generate_wisdom_quote":
                response = requests.post(f"{self.base_url}/quotes", json={
                    "input": args.get("user_input"),
                    "style": args.get("style", "inspirational")
                })
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "content": [{
                            "type": "text",
                            "text": f'"{data["quote"]}"\n\n— {data["attribution"]}\n\n{data["perspective"]}',
                            "metadata": data
                        }],
                        "isError": False
                    }
                else:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Error: {response.text}",
                            "metadata": {"error": True}
                        }],
                        "isError": True
                    }
        
        return {"error": {"code": -32601, "message": "Method not found"}}

mcp = PerspectiveShifterMCP()

# Read JSON-RPC messages from stdin
for line in sys.stdin:
    try:
        request = json.loads(line.strip())
        response = {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": mcp.handle_request(request)
        }
        print(json.dumps(response))
        sys.stdout.flush()
    except Exception as e:
        error_response = {
            "jsonrpc": "2.0",
            "id": request.get("id") if 'request' in locals() else None,
            "error": {"code": -32603, "message": str(e)}
        }
        print(json.dumps(error_response))
        sys.stdout.flush()
"""]
            }
        }
    }


async def run_stdio_server():
    """
    Run MCP server using stdio transport for Claude Desktop.
    
    This function handles JSON-RPC messages over stdin/stdout.
    """
    import sys
    
    logger.info("Starting PerspectiveShifter MCP server...")
    
    try:
        # Read JSON-RPC messages from stdin
        for line in sys.stdin:
            try:
                # Parse JSON-RPC request
                request = json.loads(line.strip())
                
                # Handle the request
                response = mcp_server.handle_request(request)
                
                # Send response to stdout
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                
                print(json.dumps(error_response))
                sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        logger.info("MCP server shutting down...")
    except Exception as e:
        logger.error(f"Fatal server error: {str(e)}")


if __name__ == "__main__":
    # Run the MCP server
    asyncio.run(run_stdio_server())