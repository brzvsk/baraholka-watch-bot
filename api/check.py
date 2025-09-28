from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging

# Add the parent directory to Python path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from main import BaraholkaBot

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Configure logging for serverless environment
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            # Initialize and run the bot
            bot = BaraholkaBot()
            
            # Run once to check for new products
            bot.run_once()
            
            # Get stats
            stats = bot.get_stats()
            
            response = {
                "status": "success",
                "message": "Bot check completed successfully",
                "stats": stats
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e)
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_POST(self):
        # Handle POST requests the same way as GET for simplicity
        self.do_GET()