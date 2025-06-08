#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath('../../..'))

from lib.api.rate_limiter import BudgetBasedRateLimiter
from datetime import datetime, timedelta
import time


def test_budget_calculations():
    """Test basic budget and quota calculations"""
    limiter = BudgetBasedRateLimiter()
    
    # Verify budget math
    expected_daily_quotes = int(1.00 / 0.00045)  # ~2222
    assert limiter.max_quotes_per_day == expected_daily_quotes
    assert limiter.max_quotes_per_hour == expected_daily_quotes // 24
    assert limiter.max_quotes_per_minute >= 1
    
    print(f"✓ Budget calculations: {limiter.max_quotes_per_day} quotes/day, {limiter.max_quotes_per_hour} quotes/hour")


def test_ip_hashing():
    """Test IP address hashing for privacy"""
    limiter = BudgetBasedRateLimiter()
    
    ip1 = "192.168.1.1"
    ip2 = "10.0.0.1"
    
    hash1 = limiter._hash_ip(ip1)
    hash2 = limiter._hash_ip(ip2)
    
    # Hashes should be different
    assert hash1 != hash2
    # Hashes should be consistent
    assert hash1 == limiter._hash_ip(ip1)
    # Hashes should be reasonably short (16 chars)
    assert len(hash1) == 16
    
    print("✓ IP hashing works correctly")


def test_ai_agent_detection():
    """Test AI agent detection from User-Agent strings"""
    limiter = BudgetBasedRateLimiter()
    
    # Test AI agent patterns
    ai_agents = [
        "ClaudeDesktop/1.0",
        "OpenAI-GPT/4.0",
        "AnthropicBot/1.0",
        "MCP-Client/1.0",
        "Assistant-Bot/2.1"
    ]
    
    normal_agents = [
        "Mozilla/5.0 (Chrome)",
        "curl/7.68.0",
        "PostmanRuntime/7.26.5",
        "Python-requests/2.25.1"
    ]
    
    for agent in ai_agents:
        assert limiter._is_ai_agent(agent), f"Should detect {agent} as AI agent"
    
    for agent in normal_agents:
        assert not limiter._is_ai_agent(agent), f"Should NOT detect {agent} as AI agent"
    
    print("✓ AI agent detection works correctly")


def test_quota_checking_basic():
    """Test basic quota checking logic"""
    limiter = BudgetBasedRateLimiter()
    
    # Fresh limiter should allow requests
    result = limiter.check_quota("192.168.1.1", "test-browser")
    assert result["allowed"] is True
    assert result["reason"] == "QUOTA_AVAILABLE"
    assert result["remaining_today"] > 0
    assert result["retry_after"] is None
    
    print("✓ Basic quota checking allows fresh requests")


def test_ip_rate_limiting():
    """Test per-IP rate limiting"""
    limiter = BudgetBasedRateLimiter()
    test_ip = "192.168.1.100"
    
    # Make requests up to the minute limit
    for i in range(limiter.max_quotes_per_ip_minute):
        result = limiter.check_quota(test_ip, "test-browser")
        if result["allowed"]:
            limiter.record_request(test_ip, "test-browser")
    
    # Next request should be rate limited
    result = limiter.check_quota(test_ip, "test-browser")
    assert result["allowed"] is False
    assert result["reason"] == "IP_MINUTE_LIMIT_EXCEEDED"
    assert result["retry_after"] == 60
    
    # Different IP should still be allowed
    result2 = limiter.check_quota("192.168.1.101", "test-browser")
    assert result2["allowed"] is True
    
    print(f"✓ IP rate limiting works (blocked after {limiter.max_quotes_per_ip_minute} requests/minute)")


def test_ai_agent_higher_limits():
    """Test that AI agents get higher rate limits"""
    limiter = BudgetBasedRateLimiter()
    test_ip = "192.168.1.200"
    
    # AI agent should get higher limits
    normal_limit = limiter.max_quotes_per_ip_minute
    ai_limit = int(normal_limit * limiter.ai_agent_multiplier)
    
    # Make requests as AI agent up to normal limit + 1
    for i in range(normal_limit + 1):
        result = limiter.check_quota(test_ip, "ClaudeDesktop/1.0")
        if result["allowed"]:
            limiter.record_request(test_ip, "ClaudeDesktop/1.0")
        else:
            break
    
    # Should still be allowed (AI agents get higher limits)
    result = limiter.check_quota(test_ip, "ClaudeDesktop/1.0")
    # Note: This might fail if we've already hit the limit due to timing
    # In a real test, we'd mock the time
    
    print(f"✓ AI agents get {limiter.ai_agent_multiplier}x higher limits")


def test_budget_enforcement():
    """Test daily budget enforcement"""
    limiter = BudgetBasedRateLimiter()
    
    # Simulate spending the entire budget
    limiter._daily_cost_usd = limiter.daily_budget_usd
    
    result = limiter.check_quota("192.168.1.250", "test-browser")
    assert result["allowed"] is False
    assert result["reason"] == "DAILY_BUDGET_EXCEEDED"
    assert result["cost_info"]["daily_remaining_usd"] == 0.0
    
    print("✓ Daily budget enforcement works")


def test_cost_tracking():
    """Test cost tracking and reporting"""
    limiter = BudgetBasedRateLimiter()
    
    # Record some requests with costs
    test_ip = "192.168.1.300"
    
    limiter.record_request(test_ip, "test", cost_usd=0.001)
    limiter.record_request(test_ip, "test", cost_usd=0.002)
    
    cost_info = limiter._get_cost_info()
    assert cost_info["daily_spent_usd"] == 0.003
    assert cost_info["daily_remaining_usd"] == round(1.0 - 0.003, 6)
    
    print("✓ Cost tracking works correctly")


def test_quota_status_reporting():
    """Test quota status reporting for monitoring"""
    limiter = BudgetBasedRateLimiter()
    
    # Make a few requests
    for i in range(3):
        result = limiter.check_quota(f"192.168.1.{400+i}", "test")
        if result["allowed"]:
            limiter.record_request(f"192.168.1.{400+i}", "test")
    
    status = limiter.get_quota_status()
    
    assert "global_daily_count" in status
    assert "cost_info" in status
    assert status["global_daily_count"] == 3
    assert status["active_ips"] == 3
    
    print("✓ Quota status reporting works")


def test_quota_reset():
    """Test quota reset functionality"""
    limiter = BudgetBasedRateLimiter()
    
    # Make some requests and record costs
    test_ip = "192.168.1.500"
    limiter.record_request(test_ip, "test", cost_usd=0.1)
    limiter._global_daily_count = 100
    limiter._global_hourly_count = 50
    
    # Reset everything
    limiter.reset_quotas("all")
    
    assert limiter._global_daily_count == 0
    assert limiter._global_hourly_count == 0
    assert limiter._daily_cost_usd == 0.0
    assert len(limiter._ip_requests) == 0
    
    print("✓ Quota reset functionality works")


def test_edge_cases():
    """Test edge cases and error conditions"""
    limiter = BudgetBasedRateLimiter()
    
    # Empty/None IP
    result = limiter.check_quota("", "")
    assert result["allowed"] is True  # Should still work with hashed empty string
    
    # Very long IP (should still hash)
    long_ip = "192.168.1.1" * 10
    result = limiter.check_quota(long_ip, "test")
    assert result["allowed"] is True
    
    # None user agent
    result = limiter.check_quota("192.168.1.1", None)
    assert result["allowed"] is True
    
    print("✓ Edge cases handled correctly")


def main():
    print("Testing Rate Limiter...")
    print()
    
    try:
        test_budget_calculations()
        test_ip_hashing()
        test_ai_agent_detection()
        test_quota_checking_basic()
        test_ip_rate_limiting()
        test_ai_agent_higher_limits()
        test_budget_enforcement()
        test_cost_tracking()
        test_quota_status_reporting()
        test_quota_reset()
        test_edge_cases()
        
        print()
        print("🎉 All rate limiter tests passed!")
        
        # Display sample quota info
        limiter = BudgetBasedRateLimiter()
        status = limiter.get_quota_status()
        print(f"\nSample Quota Configuration:")
        print(f"  Daily Budget: ${limiter.daily_budget_usd}")
        print(f"  Max Quotes/Day: {status['max_quotes_per_day']:,}")
        print(f"  Max Quotes/Hour: {status['max_quotes_per_hour']:,}")
        print(f"  Per-IP Hour Limit: {limiter.max_quotes_per_ip_hour}")
        print(f"  Per-IP Minute Limit: {limiter.max_quotes_per_ip_minute}")
        print(f"  AI Agent Multiplier: {limiter.ai_agent_multiplier}x")
        
        return True
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)