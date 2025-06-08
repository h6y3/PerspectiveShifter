"""
POST /api/v1/quotes - Generate wisdom quotes API endpoint

Vercel serverless function using the correct BaseHTTPRequestHandler pattern.
"""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for quote generation"""
        try:
            # Set CORS headers
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Get request body
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_error_response(400, "Invalid JSON")
                return
            
            # Validate input
            user_input = request_data.get('input', '').strip()
            if not user_input or len(user_input) < 3:
                self.send_error_response(400, "Input too short (minimum 3 characters)")
                return
            
            if len(user_input) > 500:
                self.send_error_response(400, "Input too long (maximum 500 characters)")
                return
            
            # For now, return a basic response since the full service layer has import issues
            style = request_data.get('style', 'inspirational')
            quote_id = f"api_{int(datetime.utcnow().timestamp())}"
            
            response_data = {
                "quote_id": quote_id,
                "quote": f"Every challenge in '{user_input}' is an opportunity for growth.",
                "attribution": "API Test Response",
                "perspective": f"A {style} perspective on your situation",
                "context": f"Generated for: {user_input}",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "image_url": f"https://theperspectiveshift.vercel.app/api/v1/images/{quote_id}",
                "metadata": {
                    "style": style,
                    "processing_time_ms": 150,
                    "source": "api_fallback"
                }
            }
            
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())
    
    def do_GET(self):
        """Handle GET requests for quote retrieval by ID"""
        try:
            # Extract quote_id from path
            path_parts = self.path.split('/')
            if len(path_parts) >= 4 and path_parts[-1]:
                quote_id = path_parts[-1]
                
                # Set CORS headers
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                # Return basic quote data (normally would fetch from database)
                response_data = {
                    "quote_id": quote_id,
                    "quote": "This is a retrieved quote for testing.",
                    "attribution": "Test Author",
                    "perspective": "Test perspective",
                    "context": "Retrieved from API",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "image_url": f"https://theperspectiveshift.vercel.app/api/v1/images/{quote_id}"
                }
                
                self.wfile.write(json.dumps(response_data, indent=2).encode())
            else:
                self.send_error_response(400, "Quote ID required")
                
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
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