from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import requests
import json
import time
import os
from dotenv import load_dotenv
import threading
from datetime import datetime
import io

load_dotenv()

app = Flask(__name__)
CORS(app)

# Store the last activity timestamp
last_activity = datetime.now()

def get_result(request_id):
    """Get the result directly using the request ID."""
    try:
        headers = {
            'Accept-Language': 'en-GB',
            'X-Fal-Target-Url': f'https://queue.fal.run/fal-ai/fast-turbo-diffusion/requests/{request_id}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://chroma-neon.vercel.app',
            'Referer': 'https://chroma-neon.vercel.app/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36'
        }
        
        response = requests.get(
            'https://chroma-neon.vercel.app/api/fal/proxy',
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        print(f"Failed to get result: {response.status_code}")
        return None
    except Exception as e:
        print(f"Error getting result: {str(e)}")
        return None

def poll_result(request_id, max_retries=30, delay=1):
    """Poll until the image is ready or max retries is reached."""
    for _ in range(max_retries):
        try:
            headers = {
                'Accept-Language': 'en-GB',
                'X-Fal-Target-Url': f'https://queue.fal.run/fal-ai/fast-turbo-diffusion/requests/{request_id}/status',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'https://chroma-neon.vercel.app',
                'Referer': 'https://chroma-neon.vercel.app/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36'
            }
            
            status_response = requests.get(
                'https://chroma-neon.vercel.app/api/fal/proxy',
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Status check response: {json.dumps(status_data, indent=2)}")
                
                if status_data.get('status') == 'COMPLETED':
                    result = get_result(request_id)
                    if result:
                        return result
                        
                elif status_data.get('status') in ['FAILED', 'CANCELLED']:
                    return {'error': f"Generation {status_data.get('status').lower()}"}
                    
                print(f"Status: {status_data.get('status', 'unknown')}, retrying...")
            time.sleep(delay)
        except Exception as e:
            print(f"Error polling status: {str(e)}")
    return {'error': 'Timeout waiting for image generation'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    global last_activity
    last_activity = datetime.now()
    return jsonify({
        "status": "healthy",
        "last_activity": last_activity.isoformat()
    })

@app.route('/generate', methods=['POST'])
def generate():
    global last_activity
    last_activity = datetime.now()
    
    try:
        data = request.json
        print("Received request data:", json.dumps(data, indent=2))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Fal-Target-Url': 'https://queue.fal.run/fal-ai/fast-turbo-diffusion',
            'Accept-Language': 'en-GB',
            'Origin': 'https://chroma-neon.vercel.app',
            'Referer': 'https://chroma-neon.vercel.app/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36',
            'Priority': 'u=1, i'
        }
        
        # Initial request to get queue status
        response = requests.post(
            'https://chroma-neon.vercel.app/api/fal/proxy',
            json=data,
            headers=headers
        )
        
        if response.status_code != 200:
            error_msg = f'Proxy request failed with status {response.status_code}'
            try:
                error_data = response.json()
                error_msg += f': {json.dumps(error_data)}'
            except:
                error_msg += f': {response.text}'
            return jsonify({'error': error_msg}), response.status_code
        
        initial_data = response.json()
        print("Initial response data:", json.dumps(initial_data, indent=2))
        
        if initial_data.get('status') == 'IN_QUEUE':
            request_id = initial_data.get('request_id')
            if not request_id:
                return jsonify({'error': 'No request ID provided'}), 500
                
            print(f"Request ID: {request_id}")
            result = poll_result(request_id)
            
            if 'error' in result:
                return jsonify(result), 500
                
            print("Final result:", json.dumps(result, indent=2))
            return jsonify(result)
        
        return jsonify(initial_data)
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-image', methods=['GET'])
def generate_image():
    global last_activity
    last_activity = datetime.now()
    
    try:
        # Get the prompt text from query parameter
        text = request.args.get('text', '')
        if not text:
            return jsonify({'error': 'No text prompt provided'}), 400
            
        # Create request to the new service
        url = f'https://fast-flux-demo.replicate.workers.dev/api/generate-image'
        headers = {
            'Sec-Ch-Ua-Platform': 'Windows',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Sec-Ch-Ua': '"Not:A-Brand";v="24", "Chromium";v="134"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Sec-Ch-Ua-Mobile': '?0',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Dest': 'image',
            'Referer': 'https://fast-flux-demo.replicate.workers.dev/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Priority': 'i'
        }
        
        params = {'text': text}
        
        # Make the request and stream the response directly
        response = requests.get(url, headers=headers, params=params, stream=True)
        
        if response.status_code != 200:
            return jsonify({'error': f'Image generation failed with status {response.status_code}'}), response.status_code
            
        # Return the image directly to the client
        return send_file(
            io.BytesIO(response.content),
            mimetype=response.headers.get('Content-Type', 'image/jpeg'),
            as_attachment=False
        )
            
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return jsonify({'error': str(e)}), 500

def ping_service():
    """Background task to ping the service periodically"""
    while True:
        try:
            # Get the service URL from environment or use a default
            service_url = os.getenv('SERVICE_URL', 'https://pranavai.onrender.com')
            response = requests.get(f"{service_url}/health")
            print(f"Health check response: {response.status_code}")
            time.sleep(300)  # Ping every 5 minutes
        except Exception as e:
            print(f"Error in health check: {e}")
            time.sleep(300)  # Wait before retrying

def start_background_task():
    """Start the background ping task"""
    thread = threading.Thread(target=ping_service, daemon=True)
    thread.start()

# Start the background task when the app starts
start_background_task()
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')