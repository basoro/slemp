from flask import Flask, jsonify
import sys
import os

# Add the current directory to Python path to import from index.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import functions from index.py
from index import generate_response, get_ollama_status, get_models, pull_model, delete_model, get_config, update_config

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/plugins/ollama/generate', methods=['POST'])
def api_generate():
    """HTTP API endpoint to generate response via Ollama CLI"""
    return generate_response()

@app.route('/api/plugins/ollama/status', methods=['GET'])
def api_status():
    """HTTP API endpoint to get Ollama status"""
    return get_ollama_status()

@app.route('/api/plugins/ollama/models', methods=['GET'])
def api_models():
    """HTTP API endpoint to get available models"""
    return get_models()

@app.route('/api/plugins/ollama/models', methods=['POST'])
def api_pull_model():
    """HTTP API endpoint to pull/download a model"""
    return pull_model()

@app.route('/api/plugins/ollama/models', methods=['DELETE'])
def api_delete_model():
    """HTTP API endpoint to delete a model"""
    return delete_model()

@app.route('/api/plugins/ollama/config', methods=['GET'])
def api_get_config():
    """HTTP API endpoint to get configuration"""
    return get_config()

@app.route('/api/plugins/ollama/config', methods=['POST'])
def api_update_config():
    """HTTP API endpoint to update configuration"""
    return update_config()

@app.route('/status', methods=['GET'])
def api_simple_status():
    """Simple HTTP API endpoint to check if server is running"""
    return {'status': 'running', 'port': 5001}

@app.route('/status', methods=['OPTIONS'])
def api_simple_status_options():
    """Handle OPTIONS request for CORS preflight"""
    return '', 200

if __name__ == '__main__':
    print("Starting Ollama HTTP API server on port 5001...")
    # Jalankan Flask server di port 5001, bisa diubah sesuai kebutuhan
    app.run(host='0.0.0.0', port=5001, debug=False)
