from flask import Blueprint, request, jsonify
import requests
import json
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp_bp = Blueprint('mcp', __name__)

# n8n API configuration - will be set from environment variables
N8N_API_URL = None
N8N_API_KEY = None
AUTH_TOKEN = None

def init_config():
    """Initialize configuration from environment variables"""
    global N8N_API_URL, N8N_API_KEY, AUTH_TOKEN
    import os
    N8N_API_URL = os.getenv('N8N_API_URL', 'http://n8n:5678' )
    N8N_API_KEY = os.getenv('N8N_API_KEY')
    AUTH_TOKEN = os.getenv('AUTH_TOKEN')
    
    logger.info(f"Initialized with N8N_API_URL: {N8N_API_URL}")
    logger.info(f"N8N_API_KEY configured: {'Yes' if N8N_API_KEY else 'No'}")
    logger.info(f"AUTH_TOKEN configured: {'Yes' if AUTH_TOKEN else 'No'}")

def authenticate_request():
    """Verify the request has valid authentication"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not AUTH_TOKEN:
        return False
    
    # Support both "Bearer token" and "Bearer token" formats
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        token = auth_header
    
    return token == AUTH_TOKEN

def make_n8n_request(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Make a request to the n8n API with proper authentication"""
    if not N8N_API_KEY:
        raise ValueError("N8N_API_KEY not configured")
    
    url = f"{N8N_API_URL}/api/v1{endpoint}"
    headers = {
        'X-N8N-API-KEY': N8N_API_KEY,
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Making {method} request to {url}")
    if data:
        logger.info(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code >= 400:
            logger.error(f"n8n API error: {response.text}")
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        raise

@mcp_bp.route('/mcp', methods=['POST'])
def handle_mcp_request():
    """Handle MCP requests from MCPO"""
    init_config()
    
    # Authenticate the request
    if not authenticate_request():
        logger.warning("Unauthorized request")
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        mcp_data = request.get_json()
        logger.info(f"Received MCP request: {json.dumps(mcp_data, indent=2)}")
        
        # Handle different MCP request types
        if 'method' in mcp_data:
            method = mcp_data['method']
            
            if method == 'tools/list':
                return handle_tools_list()
            elif method == 'tools/call':
                return handle_tool_call(mcp_data)
            else:
                logger.warning(f"Unknown MCP method: {method}")
                return jsonify({'error': f'Unknown method: {method}'}), 400
        else:
            logger.warning("Invalid MCP request format")
            return jsonify({'error': 'Invalid MCP request format'}), 400
            
    except Exception as e:
        logger.error(f"Error handling MCP request: {str(e)}")
        return jsonify({'error': str(e)}), 500

def handle_tools_list():
    """Return the list of available n8n tools"""
    tools = [
        {
            "name": "n8n_create_workflow",
            "description": "Create a new workflow in n8n",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Workflow name"},
                    "nodes": {"type": "array", "description": "Array of workflow nodes"},
                    "connections": {"type": "object", "description": "Node connections"},
                    "active": {"type": "boolean", "description": "Whether to activate the workflow"}
                },
                "required": ["name", "nodes", "connections"]
            }
        },
        {
            "name": "n8n_list_workflows",
            "description": "List all workflows in n8n",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "n8n_get_workflow",
            "description": "Get a specific workflow by ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Workflow ID"}
                },
                "required": ["id"]
            }
        }
    ]
    
    return jsonify({
        "tools": tools
    })

def handle_tool_call(mcp_data: Dict[Any, Any]):
    """Handle tool call requests"""
    if 'params' not in mcp_data:
        return jsonify({'error': 'Missing params in tool call'}), 400
    
    params = mcp_data['params']
    tool_name = params.get('name')
    arguments = params.get('arguments', {})
    
    logger.info(f"Calling tool: {tool_name} with arguments: {json.dumps(arguments, indent=2)}")
    
    try:
        if tool_name == 'n8n_create_workflow':
            return handle_create_workflow(arguments)
        elif tool_name == 'n8n_list_workflows':
            return handle_list_workflows()
        elif tool_name == 'n8n_get_workflow':
            return handle_get_workflow(arguments)
        else:
            return jsonify({'error': f'Unknown tool: {tool_name}'}), 400
            
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500

def handle_create_workflow(arguments: Dict[Any, Any]):
    """Create a new workflow using the proven API format"""
    try:
        # Extract workflow data
        name = arguments.get('name', 'Untitled Workflow')
        nodes = arguments.get('nodes', [])
        connections = arguments.get('connections', {})
        should_activate = arguments.get('active', False)
        
        # Create the workflow payload using the proven format
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
            # Note: NOT including 'active' as it's read-only during creation
        }
        
        logger.info("Creating workflow with proven API format")
        
        # Create the workflow
        workflow_result = make_n8n_request('POST', '/workflows', workflow_data)
        
        # If activation was requested, activate the workflow separately
        if should_activate and 'id' in workflow_result:
            workflow_id = workflow_result['id']
            logger.info(f"Activating workflow {workflow_id}")
            
            try:
                activation_data = {"active": True}
                updated_workflow = make_n8n_request('PUT', f'/workflows/{workflow_id}', activation_data)
                workflow_result = updated_workflow
            except Exception as e:
                logger.warning(f"Failed to activate workflow: {str(e)}")
                # Continue with the created but inactive workflow
        
        logger.info(f"Successfully created workflow: {workflow_result.get('id', 'unknown')}")
        
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully created workflow '{name}' with ID: {workflow_result.get('id', 'unknown')}"
                }
            ]
        })
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {str(e)}")
        return jsonify({
            "content": [
                {
                    "type": "text", 
                    "text": f"Failed to create workflow: {str(e)}"
                }
            ]
        }), 500

def handle_list_workflows():
    """List all workflows"""
    try:
        workflows = make_n8n_request('GET', '/workflows')
        
        workflow_list = []
        if 'data' in workflows:
            for workflow in workflows['data']:
                workflow_list.append({
                    'id': workflow.get('id'),
                    'name': workflow.get('name'),
                    'active': workflow.get('active', False),
                    'createdAt': workflow.get('createdAt'),
                    'updatedAt': workflow.get('updatedAt')
                })
        
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": f"Found {len(workflow_list)} workflows:\n" + 
                           "\n".join([f"- {w['name']} (ID: {w['id']}, Active: {w['active']})" 
                                    for w in workflow_list])
                }
            ]
        })
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": f"Failed to list workflows: {str(e)}"
                }
            ]
        }), 500

def handle_get_workflow(arguments: Dict[Any, Any]):
    """Get a specific workflow by ID"""
    try:
        workflow_id = arguments.get('id')
        if not workflow_id:
            return jsonify({'error': 'Workflow ID is required'}), 400
        
        workflow = make_n8n_request('GET', f'/workflows/{workflow_id}')
        
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": f"Workflow '{workflow.get('name', 'Unknown')}' details:\n" +
                           f"ID: {workflow.get('id')}\n" +
                           f"Active: {workflow.get('active', False)}\n" +
                           f"Nodes: {len(workflow.get('nodes', []))}\n" +
                           f"Created: {workflow.get('createdAt')}\n" +
                           f"Updated: {workflow.get('updatedAt')}"
                }
            ]
        })
        
    except Exception as e:
        logger.error(f"Failed to get workflow: {str(e)}")
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": f"Failed to get workflow: {str(e)}"
                }
            ]
        }), 500

@mcp_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'n8n-mcp-fixed',
        'n8n_configured': bool(N8N_API_KEY),
        'auth_configured': bool(AUTH_TOKEN)
    })

@mcp_bp.route('/openapi.json', methods=['GET'])
def openapi_spec():
    """Return OpenAPI specification for MCPO compatibility"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "n8n MCP Server (Fixed)",
            "version": "1.0.0",
            "description": "Fixed n8n MCP server that properly persists workflows"
        },
        "servers": [
            {"url": "/"}
        ],
        "paths": {
            "/mcp": {
                "post": {
                    "summary": "Handle MCP requests",
                    "operationId": "handle_mcp_request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    },
                    "security": [
                        {"bearerAuth": []}
                    ]
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer"
                }
            }
        }
    }
    
    return jsonify(spec )
