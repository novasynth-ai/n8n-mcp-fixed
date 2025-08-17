# n8n MCP Server (Fixed)

A fixed implementation of the n8n MCP server that properly persists workflows in n8n.

## What's Fixed

- ✅ **Workflow Persistence**: Uses the exact API format proven to work with n8n
- ✅ **Proper Authentication**: Handles Bearer token authentication correctly
- ✅ **Error Handling**: Comprehensive logging and error reporting
- ✅ **CORS Support**: Full compatibility with MCPO integration
- ✅ **Separate Activation**: Handles workflow activation as a separate API call

## Quick Deployment

### Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/n8n-mcp-fixed.git
cd n8n-mcp-fixed

# Build the Docker image
docker build -t n8n-mcp-fixed .

# Stop the existing broken n8n-mcp-server
docker stop n8n-mcp-server && docker rm n8n-mcp-server

# Deploy the fixed version
docker run -d \
  --name n8n-mcp-fixed \
  --network n8n-openweb-postgres_app-network \
  -p 3001:3000 \
  -e N8N_API_URL=http://n8n:5678 \
  -e N8N_API_KEY=your_n8n_api_key \
  -e AUTH_TOKEN=your_auth_token \
  --restart unless-stopped \
  n8n-mcp-fixed

# Update MCPO to point to the fixed server
docker stop mcpo && docker rm mcpo
docker run -d \
  --name mcpo \
  --network n8n-openweb-postgres_app-network \
  -p 8001:8002 \
  ghcr.io/open-webui/mcpo:main \
  --port 8002 \
  --api-key "your_mcpo_api_key" \
  --server-type "streamable-http" \
  --header '{"Authorization": "Bearer your_auth_token"}' \
  -- \
  http://n8n-mcp-fixed:3000/mcp
```

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `N8N_API_URL` | n8n instance URL | Yes | `http://n8n:5678` |
| `N8N_API_KEY` | n8n API key | Yes | `eyJhbGciOiJIUzI1NiIs...` |
| `AUTH_TOKEN` | MCP server auth token | Yes | `6dZye17Z4/zwaBw4Wk0DpNaWGusljfHC3aba/nHrac8=` |

## Verification

### Health Check
```bash
curl http://localhost:3001/health
```

### Test Workflow Creation
```bash
curl -X POST http://localhost:3001/mcp \
  -H "Authorization: Bearer your_auth_token" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "n8n_create_workflow",
      "arguments": {
        "name": "Test Workflow",
        "nodes": [
          {
            "id": "webhook-1",
            "name": "Webhook",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [100, 300],
            "parameters": {
              "path": "test-webhook"
            }
          }
        ],
        "connections": {},
        "active": false
      }
    }
  }'
```

## Available Tools

- `n8n_create_workflow` - Create a new workflow in n8n
- `n8n_list_workflows` - List all workflows in n8n
- `n8n_get_workflow` - Get a specific workflow by ID

## API Endpoints

- `POST /mcp` - Main MCP protocol endpoint
- `GET /health` - Health check
- `GET /openapi.json` - OpenAPI specification

## Integration

This server integrates with:
- **OpenWebUI** - AI chat interface
- **MCPO** - MCP protocol bridge
- **n8n** - Workflow automation platform

The complete chain: OpenWebUI → MCPO → n8n-mcp-fixed → n8n

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if the server is running on port 3000
   - Verify network connectivity to n8n instance

2. **Authentication Errors**
   - Verify `N8N_API_KEY` is correct and valid
   - Check `AUTH_TOKEN` matches MCPO configuration

3. **Workflow Creation Fails**
   - Check n8n API logs
   - Verify n8n instance is accessible from the MCP server
   - Check server logs: `docker logs n8n-mcp-fixed`

### Logs
```bash
# Docker logs
docker logs -f n8n-mcp-fixed
```

## License

MIT License
