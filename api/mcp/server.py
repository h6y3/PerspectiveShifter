"""
MCP Server Endpoint for Vercel - PerspectiveShifter

This Vercel function provides HTTP access to the MCP server functionality,
enabling Claude Desktop and other MCP clients to connect via HTTP instead of stdio.

STRANGLER PATTERN STATUS: Phase 3 - MCP Integration
- Provides HTTP interface to MCP server
- Uses new WisdomService via MCP tools
- Enables Claude Desktop integration over HTTP
"""

import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify

from lib.mcp.server import mcp_server
from lib.api.response_formatter import APIResponse

# Initialize Flask app for Vercel
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/api/mcp/server', methods=['POST'])
def mcp_endpoint():
    """
    HTTP endpoint for MCP JSON-RPC requests.
    
    This endpoint accepts JSON-RPC 2.0 requests and forwards them
    to the MCP server for processing.
    
    Request Body: JSON-RPC 2.0 message
    Response: JSON-RPC 2.0 response
    """
    logger.info("MCP HTTP request received")
    
    try:
        # Validate request format
        if not request.is_json:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error: Request must be JSON"
                }
            }), 400
        
        # Get JSON-RPC request
        rpc_request = request.get_json()
        
        if not rpc_request:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error: Empty request body"
                }
            }), 400
        
        # Validate JSON-RPC format
        if not isinstance(rpc_request, dict) or "method" not in rpc_request:
            return jsonify({
                "jsonrpc": "2.0",
                "id": rpc_request.get("id") if isinstance(rpc_request, dict) else None,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Missing method"
                }
            }), 400
        
        # Process the request through MCP server
        logger.info(f"Processing MCP method: {rpc_request.get('method')}")
        response = mcp_server.handle_request(rpc_request)
        
        # Return JSON-RPC response
        return jsonify(response)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        }), 400
        
    except Exception as e:
        logger.error(f"MCP endpoint error: {str(e)}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": rpc_request.get("id") if 'rpc_request' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500


@app.route('/api/mcp/info', methods=['GET'])
def mcp_info():
    """
    Get MCP server information and available tools.
    
    This endpoint provides information about the MCP server
    for discovery and debugging purposes.
    """
    logger.info("MCP info request")
    
    try:
        # Get server info
        server_info = mcp_server.get_server_info()
        
        # Get available tools
        tools_info = mcp_server.list_tools()
        
        # Combine information
        info = {
            "server": server_info,
            "tools": tools_info["tools"],
            "endpoint": "/api/mcp/server",
            "protocol": "JSON-RPC 2.0 over HTTP",
            "documentation": "https://docs.anthropic.com/en/docs/build-with-claude/mcp",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return APIResponse.success(info)
        
    except Exception as e:
        logger.error(f"MCP info error: {str(e)}")
        return APIResponse.error(
            ServiceUnavailableError("MCP info unavailable"),
            500
        )


@app.route('/api/mcp/config', methods=['GET'])
def mcp_config():
    """
    Get Claude Desktop MCP configuration.
    
    This endpoint provides the configuration needed to connect
    Claude Desktop to this MCP server.
    """
    logger.info("MCP config request")
    
    try:
        # Get the base URL from the request
        base_url = request.host_url.rstrip('/')
        
        # Create HTTP-based MCP configuration
        config = {
            "mcpServers": {
                "perspectiveshifter": {
                    "command": "python",
                    "args": ["-c", f"""
import json
import requests
import sys

class HTTPMCPClient:
    def __init__(self):
        self.endpoint = "{base_url}/api/mcp/server"
    
    def send_request(self, method, params=None):
        rpc_request = {{
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {{}}
        }}
        
        try:
            response = requests.post(self.endpoint, json=rpc_request, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {{
                "jsonrpc": "2.0",
                "id": 1,
                "error": {{"code": -32603, "message": str(e)}}
            }}

client = HTTPMCPClient()

# Handle stdio JSON-RPC protocol
for line in sys.stdin:
    try:
        request = json.loads(line.strip())
        method = request.get("method")
        params = request.get("params", {{}})
        
        # Forward request to HTTP endpoint
        response = client.send_request(method, params)
        
        # Modify response ID to match request
        if "result" in response:
            response["id"] = request.get("id")
        elif "error" in response:
            response["id"] = request.get("id")
        
        print(json.dumps(response))
        sys.stdout.flush()
        
    except Exception as e:
        error_response = {{
            "jsonrpc": "2.0",
            "id": request.get("id") if 'request' in locals() else None,
            "error": {{"code": -32603, "message": str(e)}}
        }}
        print(json.dumps(error_response))
        sys.stdout.flush()
"""],
                    "env": {}
                }
            }
        }
        
        # Add setup instructions
        instructions = {
            "setup_instructions": [
                "1. Copy the 'mcpServers' configuration below",
                "2. Add it to your Claude Desktop MCP settings",
                "3. Restart Claude Desktop",
                "4. The PerspectiveShifter tools will be available in conversations"
            ],
            "tools_available": [
                "generate_wisdom_quote - Generate personalized wisdom quotes",
                "create_quote_image - Create shareable quote images", 
                "get_wisdom_quote - Retrieve quotes by ID",
                "get_system_status - Check service status"
            ]
        }
        
        return APIResponse.success({
            "config": config,
            "instructions": instructions,
            "endpoint_url": f"{base_url}/api/mcp/server",
            "info_url": f"{base_url}/api/mcp/info"
        })
        
    except Exception as e:
        logger.error(f"MCP config error: {str(e)}")
        return APIResponse.error(
            ServiceUnavailableError("MCP config unavailable"),
            500
        )


@app.route('/api/mcp/server', methods=['OPTIONS'])
@app.route('/api/mcp/info', methods=['OPTIONS'])
@app.route('/api/mcp/config', methods=['OPTIONS'])
def mcp_options():
    """Handle CORS preflight requests"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": -32603,
            "message": "Internal error"
        }
    }), 500


# Vercel handler function
def handler(request):
    """Vercel serverless function handler"""
    with app.app_context():
        return app.full_dispatch_request()


# For local development
if __name__ == '__main__':
    app.run(debug=True, port=5005)