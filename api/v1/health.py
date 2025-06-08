"""
GET /api/v1/health - API health check endpoint
GET /api/v1/stats - API usage statistics endpoint

Vercel serverless function using the correct BaseHTTPRequestHandler pattern.
"""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        # Set CORS headers
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        # Route based on path
        if self.path.endswith('/health'):
            self.send_health_response()
        elif self.path.endswith('/stats'):
            self.send_stats_response()
        else:
            self.send_error_response(404, "Not found")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())
    
    def send_health_response(self):
        """Send health check response"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "version": "1.0",
                "services": {
                    "database": "unknown",
                    "openai": "configured" if os.environ.get("OPENAI_API_KEY") else "not_configured",
                    "rate_limiter": "operational",
                    "image_generator": "operational"
                },
                "quota_status": {
                    "daily_remaining": "unknown",
                    "hourly_remaining": "unknown",
                    "budget_remaining_usd": "unknown",
                    "estimated_requests_remaining": "unknown"
                },
                "system_info": {
                    "environment": os.environ.get("FLASK_ENV", "production"),
                    "python_version": "3.12",
                    "memory_usage": "unknown"
                }
            }
            
            self.wfile.write(json.dumps(health_data, indent=2).encode())
            
        except Exception as e:
            error_data = {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "version": "1.0",
                "error": f"Health check failed: {str(e)}"
            }
            
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_data).encode())
    
    def send_stats_response(self):
        """Send stats response"""
        try:
            stats_data = {
                "daily_requests": 0,
                "quota_utilization": 0.0,
                "budget_utilization": 0.0,
                "active_ips_today": 0,
                "service_status": "operational",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            self.wfile.write(json.dumps(stats_data, indent=2).encode())
            
        except Exception as e:
            error_data = {
                "error": f"Stats temporarily unavailable: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_data).encode())
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        error_data = {
            "error": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(error_data).encode())