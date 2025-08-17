from flask import Blueprint, request, jsonify
import requests
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO )
logger = logging.getLogger(__name__)

mcp_bp = Blueprint('mcp', __name__)

N8N_API_URL = None
N8N_API_KEY = None
AUTH_TOKEN = None

def init_config():
    global N8N_API_URL, N8N_API_KEY, AUTH_TOKEN
    import os
    N8N_API_URL = os.getenv('N8N_API_URL', 'http://n8n:5678' )
    N8N_API_KEY = os.getenv('N8N_API_KEY')
    AUTH_TOKEN = os.getenv('AUTH_TOKEN')
    logger.info(f"Initialized with N8N_API_URL: {N8N_API_URL}")

def authenticate_request():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not AUTH_TOKEN:
        return False
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        token = auth_header
    return token == AUTH_TOKEN

@mcp_bp.route('/mcp', methods=['OPTIONS'])
def handle_mcp_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@mcp_bp.route('/mcp', methods=['POST'])
def handle_mcp_request():
    init_config()
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        mcp_data = request.get_json()
        logger.info(f"Received MCP request: {json.dumps(mcp_data, indent=2)}")
        
        if 'method' in mcp_data:
            method = mcp_data['method']
            if method == 'initialize':
                return handle_initialize(mcp_data)
            elif method == 'tools/list':
                return handle_tools_list(mcp_data)
            elif method == 'tools/call':
                return handle_tool_call(mcp_data)
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": mcp_data.get("id", 0),
                    "error": {"code": -32601, "message": f"Unknown method: {method}"}
                }), 400
        else:
            return jsonify({
                "jsonrpc": "2.0", 
                "id": 0,
                "error": {"code": -32600, "message": "Invalid MCP request format"}
            }), 400
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "id": 0, 
            "error": {"code": -32603, "message": str(e)}
        }), 500

def handle_initialize(mcp_data):
    return jsonify({
        "jsonrpc": "2.0",
        "id": mcp_data.get("id", 0),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "n8n-mcp-fixed", "version": "1.0.0"}
        }
    })

def handle_tools_list(mcp_data):
    tools = [{
        "name": "n8n_create_workflow",
        "description": "Create a new workflow in n8n",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Workflow name"},
                "nodes": {"type": "array", "description": "Array of workflow nodes"},
                "connections": {"type": "object", "description": "Node connections"}
            },
            "required": ["name", "nodes", "connections"]
        }
    }]
    return jsonify({
        "jsonrpc": "2.0",
        "id": mcp_data.get("id", 0),
        "result": {"tools": tools}
    })

def handle_tool_call(mcp_data):
    if 'params' not in mcp_data:
        return jsonify({
            "jsonrpc": "2.0",
            "id": mcp_data.get("id", 0),
            "error": {"code": -32602, "message": "Missing params"}
        }), 400
    
    params = mcp_data['params']
    tool_name = params.get('name')
    arguments = params.get('arguments', {})
    
    if tool_name == 'n8n_create_workflow':
        return handle_create_workflow(arguments, mcp_data)
    else:
        return jsonify({
            "jsonrpc": "2.0",
            "id": mcp_data.get("id", 0),
            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
        }), 400

def handle_create_workflow(arguments, mcp_data):
    try:
        name = arguments.get('name', 'Untitled Workflow')
        nodes = arguments.get('nodes', [])
        connections = arguments.get('connections', {})
        
        workflow_data = {
            "name": name,
            "nodes": nodes,
            "connections": connections,
            "settings": {
                "executionOrder": "v1",
                "saveDataErrorExecution": "all",
                "saveDataSuccessExecution": "all",
                "saveManualExecutions": True,
                "saveExecutionProgress": True
            }
        }
        
        url = f"{N8N_API_URL}/api/v1/workflows"
        headers = {'X-N8N-API-KEY': N8N_API_KEY, 'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, json=workflow_data)
        response.raise_for_status()
        workflow_result = response.json()
        
        return jsonify({
            "jsonrpc": "2.0",
            "id": mcp_data.get("id", 0),
            "result": {
                "content": [{
                    "type": "text",
                    "text": f"Successfully created workflow '{name}' with ID: {workflow_result.get('id', 'unknown')}"
                }]
            }
        })
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "id": mcp_data.get("id", 0),
            "error": {"code": -32603, "message": f"Failed to create workflow: {str(e)}"}
        }), 500

@mcp_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'n8n-mcp-fixed',
        'n8n_configured': bool(N8N_API_KEY),
        'auth_configured': bool(AUTH_TOKEN)
    })
