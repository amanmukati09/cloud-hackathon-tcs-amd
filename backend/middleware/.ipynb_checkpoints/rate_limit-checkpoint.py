# backend/middleware/rate_limit.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from cache import _redis
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60, exempt_paths: list = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.exempt_paths = exempt_paths or [
            "/auth/login",
            "/auth/register",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip exempt paths
        for path in self.exempt_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        # Get user identifier (token or IP)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            user_id = auth_header.split(" ")[1][:20]  # First 20 chars of token
        else:
            user_id = request.client.host if request.client else "unknown"
        
        # Create rate limit key (per minute window)
        window = int(time.time() / 60)
        key = f"rate_limit:{user_id}:{window}"
        
        # Check and increment
        current = _redis.get(key)
        if current:
            count = int(current)
            if count >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please wait and try again.",
                        "limit": self.requests_per_minute,
                        "window": "1 minute",
                        "retry_after": 60 - (int(time.time()) % 60)
                    }
                )
            _redis.incr(key)
        else:
            _redis.setex(key, 120, 1)  # 2 min TTL for safety
        
        return await call_next(request)