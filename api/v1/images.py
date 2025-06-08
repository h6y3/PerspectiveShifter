"""
GET /api/v1/images/{quote_id} - Generate quote images API endpoint

Vercel serverless function using the correct BaseHTTPRequestHandler pattern.
"""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for image generation"""
        try:
            # Extract quote_id from path
            path_parts = self.path.split('/')
            if len(path_parts) >= 4 and path_parts[-1]:
                quote_id = path_parts[-1]
                
                # For now, redirect to the existing image endpoint since we don't have the 
                # full image generation service integrated yet
                image_url = f"https://theperspectiveshift.vercel.app/image/{quote_id}?design=3"
                
                self.send_response(302)
                self.send_header('Location', image_url)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
            else:
                self.send_error_response(400, "Quote ID required")
                
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        error_data = {
            "error": {
                "code": "API_ERROR",
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(error_data).encode())