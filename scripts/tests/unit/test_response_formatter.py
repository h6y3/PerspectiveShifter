#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath('../../..'))

from lib.api.response_formatter import (
    WisdomQuote, APIResponse, QuoteRequest, ImageRequest,
    ValidationError, RateLimitError, ServiceUnavailableError
)
from datetime import datetime
import json


def test_wisdom_quote_creation():
    quote = WisdomQuote(
        quote_id="test123",
        quote="The obstacle becomes the way.",
        attribution="Marcus Aurelius (adapted)",
        perspective="Stoic wisdom on reframing challenges",
        context="For someone feeling overwhelmed",
        style="philosophical",
        processing_time_ms=1250
    )
    
    # Test API response format
    api_response = quote.to_api_response()
    assert api_response["quote_id"] == "test123"
    assert api_response["quote"] == "The obstacle becomes the way."
    assert api_response["metadata"]["style"] == "philosophical"
    assert api_response["metadata"]["processing_time_ms"] == 1250
    assert "image_url" in api_response
    assert "created_at" in api_response
    
    # Test MCP response format
    mcp_response = quote.to_mcp_response()
    assert mcp_response["type"] == "text"
    assert "Marcus Aurelius" in mcp_response["text"]
    assert mcp_response["metadata"]["quote_id"] == "test123"
    
    # Test web format (legacy compatibility)
    web_response = quote.to_web_format()
    assert "quote_id" not in web_response  # Web format excludes ID
    assert web_response["quote"] == "The obstacle becomes the way."
    
    print("✓ WisdomQuote creation and format conversion tests passed")


def test_input_validation():
    # Valid request
    try:
        request = QuoteRequest({
            "input": "I'm feeling stressed about work",
            "style": "practical"
        })
        assert request.input == "I'm feeling stressed about work"
        assert request.style == "practical"
        assert request.include_image is True  # Default
        print("✓ Valid quote request validation passed")
    except Exception as e:
        print(f"✗ Valid request failed: {e}")
        return False
    
    # Test input validation errors
    test_cases = [
        ({"input": ""}, "Input too short"),
        ({"input": None}, "Input is required"),
        ({"input": 123}, "Input must be a string"),
        ({"input": "a" * 501}, "Input too long"),
        ({"input": "valid input", "style": "invalid"}, "Invalid style"),
        ({"input": "valid input", "style": 123}, "Style must be a string"),
    ]
    
    for test_data, expected_error in test_cases:
        try:
            QuoteRequest(test_data)
            print(f"✗ Expected validation error for {test_data}")
            return False
        except ValidationError as e:
            if expected_error not in e.message:
                print(f"✗ Wrong error message. Expected '{expected_error}', got '{e.message}'")
                return False
    
    print("✓ Input validation error tests passed")


def test_image_request_validation():
    # Valid request
    try:
        request = ImageRequest({"quote_id": "test123", "design": 2})
        assert request.quote_id == "test123"
        assert request.design == 2
        print("✓ Valid image request validation passed")
    except Exception as e:
        print(f"✗ Valid image request failed: {e}")
        return False
    
    # Test validation errors
    error_cases = [
        ({"quote_id": ""}, "Quote ID cannot be empty"),
        ({"quote_id": None}, "Quote ID is required"),
        ({"quote_id": "valid", "design": 0}, "Design must be between 1 and 4"),
        ({"quote_id": "valid", "design": 5}, "Design must be between 1 and 4"),
        ({"quote_id": "valid", "design": "invalid"}, "Design must be an integer"),
    ]
    
    for test_data, expected_error in error_cases:
        try:
            ImageRequest(test_data)
            print(f"✗ Expected validation error for {test_data}")
            return False
        except ValidationError as e:
            if expected_error not in e.message:
                print(f"✗ Wrong error message. Expected '{expected_error}', got '{e.message}'")
                return False
    
    print("✓ Image request validation error tests passed")


def test_api_responses():
    # Test success response
    quote = WisdomQuote(
        quote_id="test123",
        quote="Test quote",
        attribution="Test Author",
        perspective="Test perspective",
        context="Test context"
    )
    
    success_response = APIResponse.success(quote)
    assert success_response["status_code"] == 200
    assert success_response["headers"]["Content-Type"] == "application/json"
    assert success_response["headers"]["API-Version"] == "1.0"
    
    body_data = json.loads(success_response["body"])
    assert body_data["quote_id"] == "test123"
    
    # Test error response
    error = ValidationError("Test error message", "test_field")
    error_response = APIResponse.error(error)
    assert error_response["status_code"] == 400
    
    error_body = json.loads(error_response["body"])
    assert error_body["error"]["code"] == "VALIDATION_ERROR"
    assert error_body["error"]["message"] == "Test error message"
    assert error_body["error"]["details"]["field"] == "test_field"
    
    # Test rate limit response
    rate_limit_response = APIResponse.rate_limit(60, "2025-06-08T13:00:00Z")
    assert rate_limit_response["status_code"] == 429
    assert rate_limit_response["headers"]["Retry-After"] == "60"
    
    rate_limit_body = json.loads(rate_limit_response["body"])
    assert rate_limit_body["error"]["code"] == "RATE_LIMITED"
    assert rate_limit_body["error"]["details"]["retry_after"] == 60
    
    print("✓ API response format tests passed")


def test_legacy_compatibility():
    # Test conversion from legacy openai_service format
    legacy_data = {
        "quote": "Legacy quote text",
        "attribution": "Legacy Author",
        "perspective": "Legacy perspective",
        "context": "Legacy context"
    }
    
    quote = WisdomQuote.from_legacy_response(
        legacy_data, 
        quote_id="legacy123",
        style="practical",
        processing_time_ms=800
    )
    
    assert quote.quote_id == "legacy123"
    assert quote.quote == "Legacy quote text"
    assert quote.style == "practical"
    assert quote.processing_time_ms == 800
    
    # Ensure it can convert to all formats
    api_format = quote.to_api_response()
    web_format = quote.to_web_format()
    mcp_format = quote.to_mcp_response()
    
    assert all([api_format, web_format, mcp_format])
    print("✓ Legacy compatibility tests passed")


def main():
    print("Testing API response formatter...")
    print()
    
    try:
        test_wisdom_quote_creation()
        test_input_validation()
        test_image_request_validation()
        test_api_responses()
        test_legacy_compatibility()
        
        print()
        print("🎉 All response formatter tests passed!")
        return True
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)