import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time
from collections import defaultdict, deque


class BudgetBasedRateLimiter:
    def __init__(self):
        # Budget configuration
        self.daily_budget_usd = float(os.getenv('API_DAILY_BUDGET_USD', '1.00'))
        self.cost_per_quote = 0.00045  # Based on gpt-4o-mini pricing
        
        # Calculate quotas
        self.max_quotes_per_day = int(self.daily_budget_usd / self.cost_per_quote)
        self.max_quotes_per_hour = self.max_quotes_per_day // 24
        self.max_quotes_per_minute = max(2, self.max_quotes_per_hour // 60)  # Minimum 2/minute
        
        # Per-IP limits (configurable)
        self.max_quotes_per_ip_hour = int(os.getenv('API_MAX_QUOTES_PER_IP_HOUR', '50'))
        self.max_quotes_per_ip_minute = max(1, min(5, self.max_quotes_per_ip_hour // 60))
        
        # AI Agent detection and higher limits
        self.ai_agent_multiplier = 2.0
        self.ai_agent_patterns = [
            'claudedesktop', 'mcp', 'openai', 'anthropic',
            'gpt', 'chatgpt', 'assistant', 'bot'
        ]
        
        # In-memory tracking (will be enhanced with database later)
        self._global_daily_count = 0
        self._global_hourly_count = 0
        self._global_daily_reset = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        self._global_hourly_reset = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        # Per-IP tracking: {ip_hash: deque of timestamps}
        self._ip_requests = defaultdict(lambda: deque())
        
        # Cost tracking
        self._daily_cost_usd = 0.0
        self._cost_reset = self._global_daily_reset

    def _hash_ip(self, ip: str) -> str:
        """Create privacy-preserving hash of IP address"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def _hash_user_agent(self, user_agent: str) -> str:
        """Create privacy-preserving hash of User-Agent"""
        return hashlib.sha256(user_agent.encode()).hexdigest()[:16]

    def _is_ai_agent(self, user_agent: str) -> bool:
        """Detect if request is from an AI agent based on User-Agent"""
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in self.ai_agent_patterns)

    def _cleanup_old_requests(self, ip_hash: str, cutoff_time: datetime):
        """Remove requests older than cutoff_time for given IP"""
        requests = self._ip_requests[ip_hash]
        while requests and requests[0] < cutoff_time:
            requests.popleft()

    def _reset_global_counters_if_needed(self):
        """Reset global counters if time periods have elapsed"""
        now = datetime.utcnow()
        
        # Reset daily counters
        if now >= self._global_daily_reset + timedelta(days=1):
            self._global_daily_count = 0
            self._global_daily_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self._daily_cost_usd = 0.0
            self._cost_reset = self._global_daily_reset
        
        # Reset hourly counters
        if now >= self._global_hourly_reset + timedelta(hours=1):
            self._global_hourly_count = 0
            self._global_hourly_reset = now.replace(minute=0, second=0, microsecond=0)

    def _get_ip_request_counts(self, ip_hash: str) -> Tuple[int, int]:
        """Get current hour and minute request counts for IP"""
        now = datetime.utcnow()
        hour_cutoff = now - timedelta(hours=1)
        minute_cutoff = now - timedelta(minutes=1)
        
        # Clean up old requests
        self._cleanup_old_requests(ip_hash, hour_cutoff)
        
        # Count requests in last hour and minute
        requests = self._ip_requests[ip_hash]
        hour_count = len(requests)
        minute_count = sum(1 for req_time in requests if req_time >= minute_cutoff)
        
        return hour_count, minute_count

    def check_quota(self, client_ip: str, user_agent: str = "") -> Dict[str, any]:
        """
        Check if request is allowed based on all rate limiting rules.
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "remaining_today": int,
                "remaining_this_hour": int,
                "retry_after": Optional[int],
                "quota_reset": Optional[str],
                "cost_info": {
                    "daily_spent_usd": float,
                    "daily_remaining_usd": float,
                    "estimated_requests_remaining": int
                }
            }
        """
        self._reset_global_counters_if_needed()
        
        now = datetime.utcnow()
        ip_hash = self._hash_ip(client_ip)
        is_ai_agent = self._is_ai_agent(user_agent)
        
        # Get IP-specific request counts
        ip_hour_count, ip_minute_count = self._get_ip_request_counts(ip_hash)
        
        # Calculate effective limits for this client
        effective_ip_hour_limit = self.max_quotes_per_ip_hour
        effective_ip_minute_limit = self.max_quotes_per_ip_minute
        
        if is_ai_agent:
            effective_ip_hour_limit = int(effective_ip_hour_limit * self.ai_agent_multiplier)
            effective_ip_minute_limit = int(effective_ip_minute_limit * self.ai_agent_multiplier)

        # Check global daily budget (highest priority)
        if self._daily_cost_usd >= self.daily_budget_usd:
            next_reset = self._global_daily_reset + timedelta(days=1)
            return {
                "allowed": False,
                "reason": "DAILY_BUDGET_EXCEEDED",
                "remaining_today": 0,
                "remaining_this_hour": 0,
                "retry_after": int((next_reset - now).total_seconds()),
                "quota_reset": next_reset.isoformat() + "Z",
                "cost_info": {
                    "daily_spent_usd": self._daily_cost_usd,
                    "daily_remaining_usd": 0.0,
                    "estimated_requests_remaining": 0
                }
            }

        # Check global daily quota
        if self._global_daily_count >= self.max_quotes_per_day:
            next_reset = self._global_daily_reset + timedelta(days=1)
            return {
                "allowed": False,
                "reason": "DAILY_QUOTA_EXCEEDED",
                "remaining_today": 0,
                "remaining_this_hour": max(0, self.max_quotes_per_hour - self._global_hourly_count),
                "retry_after": int((next_reset - now).total_seconds()),
                "quota_reset": next_reset.isoformat() + "Z",
                "cost_info": self._get_cost_info()
            }

        # Check global hourly quota
        if self._global_hourly_count >= self.max_quotes_per_hour:
            next_reset = self._global_hourly_reset + timedelta(hours=1)
            return {
                "allowed": False,
                "reason": "HOURLY_QUOTA_EXCEEDED",
                "remaining_today": max(0, self.max_quotes_per_day - self._global_daily_count),
                "remaining_this_hour": 0,
                "retry_after": int((next_reset - now).total_seconds()),
                "quota_reset": next_reset.isoformat() + "Z",
                "cost_info": self._get_cost_info()
            }

        # Check per-IP hourly limit
        if ip_hour_count >= effective_ip_hour_limit:
            return {
                "allowed": False,
                "reason": "IP_HOURLY_LIMIT_EXCEEDED",
                "remaining_today": max(0, self.max_quotes_per_day - self._global_daily_count),
                "remaining_this_hour": max(0, self.max_quotes_per_hour - self._global_hourly_count),
                "retry_after": 3600,  # Try again in an hour
                "quota_reset": None,
                "cost_info": self._get_cost_info()
            }

        # Check per-IP minute limit (burst protection)
        if ip_minute_count >= effective_ip_minute_limit:
            return {
                "allowed": False,
                "reason": "IP_MINUTE_LIMIT_EXCEEDED",
                "remaining_today": max(0, self.max_quotes_per_day - self._global_daily_count),
                "remaining_this_hour": max(0, self.max_quotes_per_hour - self._global_hourly_count),
                "retry_after": 60,  # Try again in a minute
                "quota_reset": None,
                "cost_info": self._get_cost_info()
            }

        # All checks passed - request is allowed
        return {
            "allowed": True,
            "reason": "QUOTA_AVAILABLE",
            "remaining_today": max(0, self.max_quotes_per_day - self._global_daily_count - 1),
            "remaining_this_hour": max(0, self.max_quotes_per_hour - self._global_hourly_count - 1),
            "retry_after": None,
            "quota_reset": None,
            "cost_info": self._get_cost_info()
        }

    def record_request(self, client_ip: str, user_agent: str = "", cost_usd: Optional[float] = None):
        """
        Record a successful request for tracking purposes.
        Call this after a successful quote generation.
        """
        now = datetime.utcnow()
        ip_hash = self._hash_ip(client_ip)
        
        # Update global counters
        self._global_daily_count += 1
        self._global_hourly_count += 1
        
        # Update cost tracking
        actual_cost = cost_usd if cost_usd is not None else self.cost_per_quote
        self._daily_cost_usd += actual_cost
        
        # Update IP tracking
        self._ip_requests[ip_hash].append(now)

    def _get_cost_info(self) -> Dict[str, any]:
        """Get current cost information"""
        remaining_budget = max(0.0, self.daily_budget_usd - self._daily_cost_usd)
        estimated_remaining = int(remaining_budget / self.cost_per_quote)
        
        return {
            "daily_spent_usd": round(self._daily_cost_usd, 6),
            "daily_remaining_usd": round(remaining_budget, 6),
            "estimated_requests_remaining": estimated_remaining
        }

    def get_quota_status(self) -> Dict[str, any]:
        """Get current quota status for monitoring/debugging"""
        self._reset_global_counters_if_needed()
        
        return {
            "global_daily_count": self._global_daily_count,
            "global_hourly_count": self._global_hourly_count,
            "max_quotes_per_day": self.max_quotes_per_day,
            "max_quotes_per_hour": self.max_quotes_per_hour,
            "daily_reset_time": self._global_daily_reset.isoformat() + "Z",
            "hourly_reset_time": self._global_hourly_reset.isoformat() + "Z",
            "cost_info": self._get_cost_info(),
            "active_ips": len(self._ip_requests)
        }

    def reset_quotas(self, reset_type: str = "all"):
        """
        Reset quotas for testing/emergency purposes.
        reset_type: "all", "daily", "hourly", or "costs"
        """
        now = datetime.utcnow()
        
        if reset_type in ["all", "daily"]:
            self._global_daily_count = 0
            self._global_daily_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if reset_type in ["all", "hourly"]:
            self._global_hourly_count = 0
            self._global_hourly_reset = now.replace(minute=0, second=0, microsecond=0)
        
        if reset_type in ["all", "costs"]:
            self._daily_cost_usd = 0.0
            self._cost_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if reset_type == "all":
            self._ip_requests.clear()