"""
Rate limiting utility - Core features only.

Tracks API calls per IP address and enforces daily limit.
"""

from datetime import datetime, timedelta
from typing import Dict
from collections import defaultdict
from fastapi import Request, HTTPException, status


class RateLimiter:
    """
    Simple rate limiter that tracks API calls per IP address per day.
    """
    
    def __init__(self, max_calls_per_day: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls_per_day: Maximum calls per IP per day
        """
        self.max_calls_per_day = max_calls_per_day
        # Track calls: {ip: [(timestamp, ...), ...]}
        self.calls_by_ip: Dict[str, list] = defaultdict(list)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        if request.client:
            return request.client.host
        return "unknown"
    
    def check_rate_limit(self, request: Request) -> None:
        """
        Check if request exceeds daily rate limit.
        
        Raises HTTPException with 429 status if limit exceeded.
        """
        ip_address = self._get_client_ip(request)
        now = datetime.now()
        cutoff_time = now - timedelta(days=1)
        
        # Clean up old calls
        if ip_address in self.calls_by_ip:
            self.calls_by_ip[ip_address] = [
                call_time for call_time in self.calls_by_ip[ip_address]
                if call_time > cutoff_time
            ]
        
        # Count calls in last 24 hours
        recent_calls = [
            call_time for call_time in self.calls_by_ip[ip_address]
            if call_time > cutoff_time
        ]
        
        if len(recent_calls) >= self.max_calls_per_day:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {len(recent_calls)}/{self.max_calls_per_day} calls per day"
            )
        
        # Record this call
        self.calls_by_ip[ip_address].append(now)


def create_rate_limiter(rate_limit_config: dict) -> RateLimiter:
    """Create rate limiter instance from configuration."""
    rate_limit_settings = rate_limit_config.get("rate_limit", {})
    return RateLimiter(
        max_calls_per_day=rate_limit_settings.get("max_calls_per_day", 1000)
    )

