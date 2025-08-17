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
