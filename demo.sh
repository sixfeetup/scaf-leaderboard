#!/bin/bash

sessionid=$(uuidgen)

# Create a temporary Python script
cat << EOF > temp_server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
import signal

class TokenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        print(self.headers)
        
        if 'code' in query_params:
            code = query_params['code'][0]
            with open('code.txt', 'w') as f:
                f.write(code)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Token received and saved successfully!")
            # Signal the parent process
            os.kill(os.getppid(), signal.SIGUSR1)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Error: No code provided in the URL.")

def run_server(port=51111):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TokenHandler)
    print(f"Server running on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
EOF

# Function to handle the SIGUSR1 signal
code_received() {
    echo "Token received. Proceeding to next step."
    kill $server_pid
}

# Set up the signal handler
trap code_received SIGUSR1

# Start the Python server in the background
python temp_server.py &
server_pid=$!

echo "Waiting for code..."

# Example opening of the browser to auth/reg user
python -c "import webbrowser; webbrowser.open('https://scaf.withpassage.com/authorize?response_type=code&client_id=961JRDH4c4Sin8LYGGbI0Lb7&redirect_uri=http://localhost:51111&scope=openid%20email')"

# Wait for the Python script to exit
wait $server_pid

# Clean up the temporary Python script
rm temp_server.py

# Read the code
code=$(cat code.txt)
echo "Received code: $code"

# Continue with the rest of your script
echo "Proceeding with the next steps of the script..."
# Add your next steps here

# Example: Use the code in a subsequent command
# curl -v --location --request POST 'https://scaf.withpassage.com/token?grant_type=authorization_code&code=$code&redirect_uri=http%3A%2F%2Flocalhost%3A51111&client_id=961JRDH4c4Sin8LYGGbI0Lb7&client_secret=CHANGEME' \
# --header 'Content-Type: application/x-www-form-urlencoded' \
# --data ''

# write the JWT token and the sessionid to `.scaf-challenge` and into the K8s ConfigMap

# Clean up
rm code.txt

echo "Script completed."
