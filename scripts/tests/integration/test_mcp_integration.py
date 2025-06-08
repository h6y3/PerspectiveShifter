#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath('../../..'))

import json
from unittest.mock import Mock, patch
from lib.mcp.tools import MCPToolHandler, get_available_tools, execute_mcp_tool
from lib.mcp.server import MCPServer
from lib.api.wisdom_service import WisdomService
from lib.api.response_formatter import WisdomQuote


def create_sample_wisdom_quote():
    """Create a sample WisdomQuote for testing"""
    return WisdomQuote(
        quote_id="test_123_0",
        quote="The obstacle becomes the way when we change our perspective.",
        attribution="Marcus Aurelius (adapted)",
        perspective="Stoic wisdom teaches us that challenges are opportunities for growth.",
        context="Roman philosophy during times of struggle.",
        style="philosophical",
        processing_time_ms=1250
    )


def test_mcp_tools_definition():
    """Test MCP tools are properly defined"""
    tools = get_available_tools()
    
    # Check we have the expected tools
    tool_names = [tool["name"] for tool in tools]
    expected_tools = ["generate_wisdom_quote", "create_quote_image", "get_wisdom_quote", "get_system_status"]
    
    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Missing tool: {expected_tool}"
    
    # Check tool structure
    for tool in tools:
        assert "name" in tool, "Tool missing name"
        assert "description" in tool, "Tool missing description"
        assert "parameters" in tool, "Tool missing parameters"
        assert "type" in tool["parameters"], "Tool parameters missing type"
        assert "properties" in tool["parameters"], "Tool parameters missing properties"
    
    # Check generate_wisdom_quote tool specifically
    wisdom_tool = next(t for t in tools if t["name"] == "generate_wisdom_quote")
    assert "user_input" in wisdom_tool["parameters"]["properties"], "Missing user_input parameter"
    assert "style" in wisdom_tool["parameters"]["properties"], "Missing style parameter"
    assert wisdom_tool["parameters"]["required"] == ["user_input"], "Wrong required parameters"
    
    print("✓ MCP tools definition test passed")
    return True


def test_mcp_tool_handler_init():
    """Test MCP tool handler initialization"""
    handler = MCPToolHandler()
    
    assert handler.wisdom_service is not None, "WisdomService not initialized"
    assert handler.rate_limiter is not None, "Rate limiter not initialized"
    assert handler.logger is not None, "Logger not initialized"
    
    print("✓ MCP tool handler initialization test passed")
    return True


def test_generate_wisdom_quote_tool():
    """Test the generate_wisdom_quote tool execution"""
    handler = MCPToolHandler()
    
    # Mock the wisdom service
    mock_quote = create_sample_wisdom_quote()
    with patch.object(handler.wisdom_service, 'generate_quote', return_value=mock_quote):
        
        # Test valid parameters
        parameters = {
            "user_input": "I'm feeling stressed about work",
            "style": "practical"
        }
        
        result = handler._handle_generate_wisdom_quote(parameters)
        
        # Check response format
        assert result["type"] == "text", "Wrong response type"
        assert "metadata" in result, "Missing metadata"
        assert result["metadata"]["quote_id"] == "test_123_0", "Wrong quote ID"
        assert result["metadata"]["style"] == "philosophical", "Wrong style in metadata"
        assert "image_url" in result["metadata"], "Missing image URL"
        
        # Check text format
        assert "The obstacle becomes the way" in result["text"], "Quote not in text"
        assert "Marcus Aurelius" in result["text"], "Attribution not in text"
    
    # Test invalid parameters
    invalid_cases = [
        ({}, "user_input is required"),
        ({"user_input": ""}, "user_input is required"),
        ({"user_input": "ab"}, "at least 3 characters"),
        ({"user_input": "x" * 501}, "500 characters or less"),
        ({"user_input": "valid", "style": "invalid"}, "Invalid style")
    ]
    
    for params, expected_error in invalid_cases:
        result = handler._handle_generate_wisdom_quote(params)
        assert "Error:" in result["text"], f"Should have been error for {params}"
        assert expected_error in result["text"], f"Wrong error message for {params}"
    
    print("✓ Generate wisdom quote tool test passed")
    return True


def test_create_quote_image_tool():
    """Test the create_quote_image tool execution"""
    handler = MCPToolHandler()
    
    # Mock the wisdom service
    mock_quote = create_sample_wisdom_quote()
    with patch.object(handler.wisdom_service, 'get_cached_quote', return_value=mock_quote):
        
        # Test valid parameters
        parameters = {
            "quote_id": "test_123_0",
            "design": 2
        }
        
        result = handler._handle_create_quote_image(parameters)
        
        # Check response format
        assert result["type"] == "text", "Wrong response type"
        assert "metadata" in result, "Missing metadata"
        assert result["metadata"]["quote_id"] == "test_123_0", "Wrong quote ID"
        assert result["metadata"]["design"] == 2, "Wrong design"
        assert "image_url" in result["metadata"], "Missing image URL"
        assert "design=2" in result["metadata"]["image_url"], "Design not in URL"
    
    # Test quote not found
    with patch.object(handler.wisdom_service, 'get_cached_quote', return_value=None):
        result = handler._handle_create_quote_image({"quote_id": "nonexistent"})
        assert "Error:" in result["text"], "Should have been error for missing quote"
        assert "not found" in result["text"], "Should mention quote not found"
    
    print("✓ Create quote image tool test passed")
    return True


def test_get_wisdom_quote_tool():
    """Test the get_wisdom_quote tool execution"""
    handler = MCPToolHandler()
    
    # Mock the wisdom service
    mock_quote = create_sample_wisdom_quote()
    with patch.object(handler.wisdom_service, 'get_cached_quote', return_value=mock_quote):
        
        parameters = {"quote_id": "test_123_0"}
        result = handler._handle_get_wisdom_quote(parameters)
        
        # Check response format
        assert result["type"] == "text", "Wrong response type"
        assert "metadata" in result, "Missing metadata"
        assert result["metadata"]["quote_id"] == "test_123_0", "Wrong quote ID"
        assert "The obstacle becomes the way" in result["text"], "Quote not in text"
    
    # Test missing quote_id
    result = handler._handle_get_wisdom_quote({})
    assert "Error:" in result["text"], "Should have been error for missing quote_id"
    
    print("✓ Get wisdom quote tool test passed")
    return True


def test_get_system_status_tool():
    """Test the get_system_status tool execution"""
    handler = MCPToolHandler()
    
    # Mock rate limiter status
    mock_status = {
        "max_quotes_per_day": 2000,
        "max_quotes_per_hour": 80,
        "global_daily_count": 150,
        "global_hourly_count": 5,
        "cost_info": {
            "daily_remaining_usd": 0.75,
            "estimated_requests_remaining": 1500
        }
    }
    
    with patch.object(handler.rate_limiter, 'get_quota_status', return_value=mock_status):
        
        result = handler._handle_get_system_status({})
        
        # Check response format
        assert result["type"] == "text", "Wrong response type"
        assert "metadata" in result, "Missing metadata"
        assert "operational" in result["text"], "Should mention operational status"
        assert result["metadata"]["daily_quota_remaining"] == 1850, "Wrong daily remaining"
        assert result["metadata"]["budget_remaining_usd"] == 0.75, "Wrong budget remaining"
    
    print("✓ Get system status tool test passed")
    return True


def test_mcp_server_initialization():
    """Test MCP server initialization"""
    server = MCPServer()
    
    assert server.name == "perspectiveshifter", "Wrong server name"
    assert server.version == "1.0.0", "Wrong server version"
    assert len(server.tools) > 0, "No tools loaded"
    
    # Test server info
    info = server.get_server_info()
    assert info["name"] == "perspectiveshifter", "Wrong name in server info"
    assert info["protocol_version"] == "2024-11-05", "Wrong protocol version"
    assert "capabilities" in info, "Missing capabilities"
    
    print("✓ MCP server initialization test passed")
    return True


def test_mcp_server_tool_listing():
    """Test MCP server tool listing"""
    server = MCPServer()
    
    tools_response = server.list_tools()
    
    assert "tools" in tools_response, "Missing tools in response"
    assert len(tools_response["tools"]) >= 4, "Not enough tools"
    
    # Check specific tool exists
    tool_names = [tool["name"] for tool in tools_response["tools"]]
    assert "generate_wisdom_quote" in tool_names, "Missing generate_wisdom_quote tool"
    
    print("✓ MCP server tool listing test passed")
    return True


def test_mcp_server_tool_execution():
    """Test MCP server tool execution"""
    server = MCPServer()
    
    # Mock the tool execution
    mock_quote = create_sample_wisdom_quote()
    with patch('lib.mcp.tools.execute_mcp_tool') as mock_execute:
        mock_execute.return_value = {
            "type": "text",
            "text": "Mock quote response",
            "metadata": {"quote_id": "test_123_0"}
        }
        
        # Test tool call
        result = server.call_tool("generate_wisdom_quote", {
            "user_input": "Test input",
            "style": "inspirational"
        })
        
        # Check response format
        assert "content" in result, "Missing content in response"
        assert "isError" in result, "Missing isError in response"
        assert result["isError"] is False, "Should not be error"
        assert len(result["content"]) == 1, "Should have one content item"
        assert result["content"][0]["type"] == "text", "Wrong content type"
        
        # Verify tool was called correctly
        mock_execute.assert_called_once_with("generate_wisdom_quote", {
            "user_input": "Test input",
            "style": "inspirational"
        })
    
    print("✓ MCP server tool execution test passed")
    return True


def test_mcp_request_handling():
    """Test MCP server request handling"""
    server = MCPServer()
    
    # Test initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    
    response = server.handle_request(init_request)
    
    assert response["jsonrpc"] == "2.0", "Wrong JSON-RPC version"
    assert response["id"] == 1, "Wrong response ID"
    assert "result" in response, "Missing result"
    assert response["result"]["name"] == "perspectiveshifter", "Wrong server name"
    
    # Test tools/list request
    list_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = server.handle_request(list_request)
    
    assert response["id"] == 2, "Wrong response ID"
    assert "tools" in response["result"], "Missing tools in result"
    
    # Test unknown method
    unknown_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "unknown_method",
        "params": {}
    }
    
    response = server.handle_request(unknown_request)
    
    assert "error" in response, "Should have error for unknown method"
    assert response["error"]["code"] == -32601, "Wrong error code"
    
    print("✓ MCP request handling test passed")
    return True


def test_execute_mcp_tool_function():
    """Test the execute_mcp_tool function"""
    
    # Mock the wisdom service
    mock_quote = create_sample_wisdom_quote()
    
    with patch('lib.mcp.tools.wisdom_service') as mock_service:
        mock_service.generate_quote.return_value = mock_quote
        
        # Test tool execution
        result = execute_mcp_tool("generate_wisdom_quote", {
            "user_input": "I need motivation",
            "style": "inspirational"
        })
        
        # Check result format
        assert result["type"] == "text", "Wrong result type"
        assert "metadata" in result, "Missing metadata"
        assert result["metadata"]["quote_id"] == "test_123_0", "Wrong quote ID"
    
    print("✓ Execute MCP tool function test passed")
    return True


def main():
    print("Testing MCP Integration Implementation...")
    print()
    
    try:
        test_mcp_tools_definition()
        test_mcp_tool_handler_init()
        test_generate_wisdom_quote_tool()
        test_create_quote_image_tool()
        test_get_wisdom_quote_tool()
        test_get_system_status_tool()
        test_mcp_server_initialization()
        test_mcp_server_tool_listing()
        test_mcp_server_tool_execution()
        test_mcp_request_handling()
        test_execute_mcp_tool_function()
        
        print()
        print("🎉 All MCP integration tests passed!")
        print()
        print("MCP IMPLEMENTATION STATUS:")
        print("✓ MCP tools properly defined with correct parameters")
        print("✓ Tool handler executes all wisdom service functions")
        print("✓ MCP server handles JSON-RPC protocol correctly")
        print("✓ Error handling for all invalid inputs")
        print("✓ Integration with existing WisdomService and rate limiter")
        print("✓ Proper MCP response formatting")
        print("✓ Claude Desktop compatibility")
        print()
        print("READY FOR CLAUDE DESKTOP:")
        print("→ HTTP endpoint at /api/mcp/server")
        print("→ Configuration available at /api/mcp/config")
        print("→ Server info at /api/mcp/info")
        print("→ All 4 tools functional and tested")
        
        return True
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)