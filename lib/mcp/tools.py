"""
MCP Tools for PerspectiveShifter - Claude Desktop Integration

This module defines the Model Context Protocol tools that Claude Desktop
can use to interact with the PerspectiveShifter wisdom quote service.

STRANGLER PATTERN STATUS: Phase 3 - MCP Integration
- Uses new WisdomService interface
- Provides Claude Desktop with quote generation capabilities
- Integrates with rate limiting for AI agent usage
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from lib.api.wisdom_service import WisdomService
from lib.api.rate_limiter import BudgetBasedRateLimiter
from lib.api.response_formatter import ValidationError, ServiceUnavailableError

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services for MCP
rate_limiter = BudgetBasedRateLimiter()
wisdom_service = WisdomService(rate_limiter=rate_limiter)


# MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "generate_wisdom_quote",
        "description": "Generate a personalized wisdom quote based on user input or situation",
        "parameters": {
            "type": "object",
            "properties": {
                "user_input": {
                    "type": "string",
                    "description": "User's situation, feeling, challenge, or current state of mind",
                    "minLength": 3,
                    "maxLength": 500
                },
                "style": {
                    "type": "string",
                    "enum": ["inspirational", "practical", "philosophical", "humorous"],
                    "description": "Preferred wisdom style for the quote",
                    "default": "inspirational"
                }
            },
            "required": ["user_input"]
        }
    },
    {
        "name": "create_quote_image",
        "description": "Generate a shareable image for a wisdom quote",
        "parameters": {
            "type": "object",
            "properties": {
                "quote_id": {
                    "type": "string",
                    "description": "Quote ID from generate_wisdom_quote tool"
                },
                "design": {
                    "type": "integer",
                    "description": "Design template number (1-4)",
                    "minimum": 1,
                    "maximum": 4,
                    "default": 3
                }
            },
            "required": ["quote_id"]
        }
    },
    {
        "name": "get_wisdom_quote",
        "description": "Retrieve a previously generated wisdom quote by its ID",
        "parameters": {
            "type": "object",
            "properties": {
                "quote_id": {
                    "type": "string",
                    "description": "Quote ID in format 'cache_id_quote_index'"
                }
            },
            "required": ["quote_id"]
        }
    },
    {
        "name": "get_system_status",
        "description": "Get current system status and quota information for the wisdom service",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]


class MCPToolHandler:
    """Handler for MCP tool execution"""
    
    def __init__(self):
        self.wisdom_service = wisdom_service
        self.rate_limiter = rate_limiter
        self.logger = logger
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool and return formatted response.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            MCP-formatted response dict
        """
        try:
            self.logger.info(f"Executing MCP tool: {tool_name}")
            
            if tool_name == "generate_wisdom_quote":
                return self._handle_generate_wisdom_quote(parameters)
            elif tool_name == "create_quote_image":
                return self._handle_create_quote_image(parameters)
            elif tool_name == "get_wisdom_quote":
                return self._handle_get_wisdom_quote(parameters)
            elif tool_name == "get_system_status":
                return self._handle_get_system_status(parameters)
            else:
                return self._error_response(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"Error executing MCP tool {tool_name}: {str(e)}")
            return self._error_response(f"Tool execution failed: {str(e)}")
    
    def _handle_generate_wisdom_quote(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle wisdom quote generation"""
        try:
            user_input = parameters.get("user_input", "").strip()
            style = parameters.get("style", "inspirational")
            
            # Validate parameters
            if not user_input:
                return self._error_response("user_input is required")
            
            if len(user_input) < 3:
                return self._error_response("user_input must be at least 3 characters")
            
            if len(user_input) > 500:
                return self._error_response("user_input must be 500 characters or less")
            
            if style not in ["inspirational", "practical", "philosophical", "humorous"]:
                return self._error_response("Invalid style. Must be: inspirational, practical, philosophical, or humorous")
            
            # Generate quote using WisdomService
            wisdom_quote = self.wisdom_service.generate_quote(
                input_text=user_input,
                style=style,
                client_ip="127.0.0.1",  # MCP server IP
                user_agent="ClaudeDesktop/MCP",
                track_cost=True
            )
            
            # Return MCP-formatted response
            return {
                "type": "text",
                "text": f'"{wisdom_quote.quote}"\n\n— {wisdom_quote.attribution}\n\n{wisdom_quote.perspective}',
                "metadata": {
                    "quote_id": wisdom_quote.quote_id,
                    "quote": wisdom_quote.quote,
                    "attribution": wisdom_quote.attribution,
                    "perspective": wisdom_quote.perspective,
                    "context": wisdom_quote.context,
                    "style": wisdom_quote.style,
                    "image_url": f"https://app.vercel.app/api/v1/images/{wisdom_quote.quote_id}",
                    "created_at": wisdom_quote.created_at.isoformat() + "Z"
                }
            }
            
        except ValidationError as e:
            return self._error_response(f"Validation error: {e.message}")
        except ServiceUnavailableError as e:
            return self._error_response(f"Service unavailable: {e.message}")
        except Exception as e:
            self.logger.error(f"Error in generate_wisdom_quote: {str(e)}")
            return self._error_response(f"Quote generation failed: {str(e)}")
    
    def _handle_create_quote_image(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quote image creation"""
        try:
            quote_id = parameters.get("quote_id", "").strip()
            design = parameters.get("design", 3)
            
            # Validate parameters
            if not quote_id:
                return self._error_response("quote_id is required")
            
            if not isinstance(design, int) or design < 1 or design > 4:
                return self._error_response("design must be an integer between 1 and 4")
            
            # Check if quote exists
            wisdom_quote = self.wisdom_service.get_cached_quote(quote_id)
            if not wisdom_quote:
                return self._error_response(f"Quote not found: {quote_id}")
            
            # Generate image URL
            image_url = f"https://app.vercel.app/api/v1/images/{quote_id}?design={design}"
            
            return {
                "type": "text",
                "text": f"Quote image generated for: \"{wisdom_quote.quote[:50]}...\"",
                "metadata": {
                    "quote_id": quote_id,
                    "image_url": image_url,
                    "design": design,
                    "quote": wisdom_quote.quote,
                    "attribution": wisdom_quote.attribution
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in create_quote_image: {str(e)}")
            return self._error_response(f"Image creation failed: {str(e)}")
    
    def _handle_get_wisdom_quote(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quote retrieval"""
        try:
            quote_id = parameters.get("quote_id", "").strip()
            
            if not quote_id:
                return self._error_response("quote_id is required")
            
            # Retrieve quote
            wisdom_quote = self.wisdom_service.get_cached_quote(quote_id)
            if not wisdom_quote:
                return self._error_response(f"Quote not found: {quote_id}")
            
            return {
                "type": "text",
                "text": f'"{wisdom_quote.quote}"\n\n— {wisdom_quote.attribution}\n\n{wisdom_quote.perspective}',
                "metadata": {
                    "quote_id": wisdom_quote.quote_id,
                    "quote": wisdom_quote.quote,
                    "attribution": wisdom_quote.attribution,
                    "perspective": wisdom_quote.perspective,
                    "context": wisdom_quote.context,
                    "style": wisdom_quote.style,
                    "image_url": f"https://app.vercel.app/api/v1/images/{wisdom_quote.quote_id}",
                    "created_at": wisdom_quote.created_at.isoformat() + "Z"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_wisdom_quote: {str(e)}")
            return self._error_response(f"Quote retrieval failed: {str(e)}")
    
    def _handle_get_system_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system status request"""
        try:
            # Get quota status
            quota_status = self.rate_limiter.get_quota_status()
            
            status_info = {
                "service": "PerspectiveShifter Wisdom Service",
                "status": "operational",
                "daily_quota_remaining": max(0, quota_status["max_quotes_per_day"] - quota_status["global_daily_count"]),
                "hourly_quota_remaining": max(0, quota_status["max_quotes_per_hour"] - quota_status["global_hourly_count"]),
                "budget_remaining_usd": quota_status["cost_info"]["daily_remaining_usd"],
                "estimated_requests_remaining": quota_status["cost_info"]["estimated_requests_remaining"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            return {
                "type": "text",
                "text": f"PerspectiveShifter is operational.\n\nDaily quota remaining: {status_info['daily_quota_remaining']} quotes\nBudget remaining: ${status_info['budget_remaining_usd']:.2f}",
                "metadata": status_info
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_system_status: {str(e)}")
            return self._error_response(f"Status check failed: {str(e)}")
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "type": "text",
            "text": f"Error: {message}",
            "metadata": {
                "error": True,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }


# Global tool handler instance
mcp_tool_handler = MCPToolHandler()


def get_available_tools() -> List[Dict[str, Any]]:
    """Get list of available MCP tools"""
    return MCP_TOOLS


def execute_mcp_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an MCP tool.
    
    Args:
        tool_name: Name of the tool to execute
        parameters: Tool parameters
        
    Returns:
        MCP-formatted response
    """
    return mcp_tool_handler.execute_tool(tool_name, parameters)