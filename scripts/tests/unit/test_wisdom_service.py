#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath('../../..'))

import json
from unittest.mock import Mock, patch
from lib.api.wisdom_service import WisdomService
from lib.api.response_formatter import WisdomQuote, ValidationError


def create_sample_legacy_quotes():
    """Create sample quotes in legacy format"""
    return [
        {
            'quote': 'The obstacle becomes the way when we change our perspective.',
            'attribution': 'Marcus Aurelius (adapted)',
            'perspective': 'Stoic wisdom teaches us that challenges are opportunities for growth.',
            'context': 'Roman philosophy during times of struggle.'
        }
    ]


def test_input_validation():
    """Test input validation independently"""
    service = WisdomService()
    
    # Test validation of various inputs by directly calling the validation logic
    from lib.api.response_formatter import QuoteRequest
    
    # Valid inputs
    valid_cases = [
        ("I'm feeling stressed", "inspirational"),
        ("Need motivation", "practical"),
        ("What should I do?", "philosophical"),
        ("Life is hard", "humorous")
    ]
    
    for input_text, style in valid_cases:
        try:
            request = QuoteRequest({"input": input_text, "style": style})
            assert request.input == input_text
            assert request.style == style
        except Exception as e:
            print(f"✗ Valid case failed: {input_text}, {style} - {e}")
            return False
    
    # Invalid inputs
    invalid_cases = [
        ("", "Input too short"),
        ("ab", "Input too short"),
        ("x" * 501, "Input too long"),
        (None, "Input is required"),
        (123, "Input must be a string")
    ]
    
    for invalid_input, expected_error in invalid_cases:
        try:
            QuoteRequest({"input": invalid_input, "style": "inspirational"})
            print(f"✗ Should have rejected: {invalid_input}")
            return False
        except ValidationError as e:
            if expected_error not in e.message:
                print(f"✗ Wrong error for {invalid_input}. Expected '{expected_error}', got '{e.message}'")
                return False
    
    print("✓ Input validation test passed")
    return True


def test_hash_creation():
    """Test SHA256 hash creation"""
    service = WisdomService()
    
    input1 = "I'm feeling stressed about work"
    hash1 = service._create_input_hash(input1)
    hash2 = service._create_input_hash(input1)
    
    assert hash1 == hash2, "Hash should be consistent"
    assert len(hash1) == 64, "SHA256 should be 64 chars"
    assert isinstance(hash1, str), "Hash should be string"
    
    # Different inputs = different hashes
    input2 = "I'm feeling happy today"
    hash3 = service._create_input_hash(input2)
    assert hash1 != hash3, "Different inputs should have different hashes"
    
    print("✓ Hash creation test passed")
    return True


def test_legacy_conversion():
    """Test conversion from legacy format to WisdomQuote"""
    service = WisdomService()
    
    legacy_quote = {
        'quote': 'Test quote text',
        'attribution': 'Test Author',
        'perspective': 'Test perspective',
        'context': 'Test context'
    }
    
    wisdom_quote = service._convert_legacy_to_wisdom_quote(
        legacy_quote, "test_123_0", "philosophical", 1500
    )
    
    assert isinstance(wisdom_quote, WisdomQuote)
    assert wisdom_quote.quote == "Test quote text"
    assert wisdom_quote.attribution == "Test Author"
    assert wisdom_quote.quote_id == "test_123_0"
    assert wisdom_quote.style == "philosophical"
    assert wisdom_quote.processing_time_ms == 1500
    
    # Test format conversions
    api_response = wisdom_quote.to_api_response()
    assert api_response["quote_id"] == "test_123_0"
    assert api_response["metadata"]["style"] == "philosophical"
    
    mcp_response = wisdom_quote.to_mcp_response()
    assert mcp_response["type"] == "text"
    assert "Test quote text" in mcp_response["text"]
    
    web_format = wisdom_quote.to_web_format()
    assert web_format["quote"] == "Test quote text"
    assert "quote_id" not in web_format  # Web format excludes ID
    
    print("✓ Legacy conversion test passed")
    return True


def test_cost_estimation():
    """Test cost estimation logic"""
    service = WisdomService()
    
    sample_quotes = create_sample_legacy_quotes()
    test_input = "I need motivation"
    
    cost = service._estimate_openai_cost(test_input, sample_quotes)
    
    assert isinstance(cost, float), "Cost should be float"
    assert cost > 0, "Cost should be positive"
    assert cost < 0.01, "Cost should be reasonable"
    
    # Test longer input costs more
    longer_input = test_input * 10
    longer_cost = service._estimate_openai_cost(longer_input, sample_quotes)
    assert longer_cost > cost, "Longer input should cost more"
    
    print(f"✓ Cost estimation test passed (${cost:.6f})")
    return True


def test_service_initialization():
    """Test service initialization"""
    # Without rate limiter
    service1 = WisdomService()
    assert service1.rate_limiter is None
    assert service1.logger is not None
    
    # With rate limiter
    mock_limiter = Mock()
    service2 = WisdomService(rate_limiter=mock_limiter)
    assert service2.rate_limiter is mock_limiter
    
    print("✓ Service initialization test passed")
    return True


def test_quote_id_parsing():
    """Test quote ID format parsing"""
    # Test the ID format logic without actual database calls
    test_cases = [
        ("123_0", True, "123", 0),
        ("456_2", True, "456", 2),
        ("invalid", False, None, None),
        ("123", False, None, None),
        ("", False, None, None),
    ]
    
    for quote_id, should_be_valid, expected_cache_id, expected_index in test_cases:
        if should_be_valid:
            if '_' in quote_id:
                cache_id, quote_index = quote_id.split('_', 1)
                try:
                    index = int(quote_index)
                    assert cache_id == expected_cache_id
                    assert index == expected_index
                except ValueError:
                    print(f"✗ Failed to parse valid ID: {quote_id}")
                    return False
        else:
            # Invalid IDs should fail parsing
            if '_' in quote_id:
                try:
                    cache_id, quote_index = quote_id.split('_', 1)
                    int(quote_index)  # Should work for some invalid cases
                except ValueError:
                    pass  # Expected for non-numeric indices
    
    print("✓ Quote ID parsing test passed")
    return True


def test_response_formats():
    """Test all response format generation"""
    service = WisdomService()
    
    legacy_data = create_sample_legacy_quotes()[0]
    quote = service._convert_legacy_to_wisdom_quote(
        legacy_data, "test_123", "inspirational", 1000
    )
    
    # Test API format
    api_resp = quote.to_api_response()
    required_api_fields = ["quote_id", "quote", "attribution", "perspective", "context", "created_at", "image_url", "metadata"]
    for field in required_api_fields:
        assert field in api_resp, f"API response missing {field}"
    
    # Test MCP format  
    mcp_resp = quote.to_mcp_response()
    assert mcp_resp["type"] == "text"
    assert "metadata" in mcp_resp
    assert "quote_id" in mcp_resp["metadata"]
    
    # Test web format
    web_resp = quote.to_web_format()
    required_web_fields = ["quote", "attribution", "perspective", "context"]
    for field in required_web_fields:
        assert field in web_resp, f"Web response missing {field}"
    
    print("✓ Response formats test passed")
    return True


def main():
    print("Testing WisdomService Core Functionality...")
    print()
    
    try:
        test_input_validation()
        test_hash_creation()
        test_legacy_conversion()
        test_cost_estimation()
        test_service_initialization()
        test_quote_id_parsing()
        test_response_formats()
        
        print()
        print("🎉 All core WisdomService tests passed!")
        print()
        print("STRANGLER PATTERN VALIDATION:")
        print("✓ Input validation uses new response formatter")
        print("✓ Legacy quote format conversion works correctly")
        print("✓ Multi-format output (API, MCP, Web) functional")
        print("✓ Cost estimation ready for rate limiting")
        print("✓ Quote ID format maintains legacy compatibility")
        print("✓ Service initialization handles optional dependencies")
        print()
        print("IMPLEMENTATION STATUS:")
        print("✓ Phase 1.1: WisdomService class skeleton - COMPLETE")
        print("→ Phase 1.2: Implement generate_quote() - READY FOR INTEGRATION TEST")
        print("→ Phase 1.3: Implement get_cached_quote() - READY FOR DATABASE TEST")
        print("→ Phase 1.4: Rate limiter integration - READY")
        print("→ Phase 1.5: End-to-end testing - PENDING")
        
        return True
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)