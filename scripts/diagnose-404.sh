#!/bin/bash
# Diagnose 404 errors with ngrok + MCP setup

echo "🔍 MCP Server + ngrok Diagnostic Tool"
echo "======================================"
echo ""

# Check if servers are running
echo "1. Checking if MCP servers are running..."
if ps aux | grep -q "[s]erver.py"; then
    echo "   ✅ MCP servers are running"
    ps aux | grep "[s]erver.py" | awk '{print "      PID", $2, "-", $NF}'
else
    echo "   ❌ MCP servers are NOT running"
    echo "   Run: bash start-mcp-http.sh"
    exit 1
fi
echo ""

# Check if ports are listening
echo "2. Checking if ports are listening..."
for port in 9001 9002 9003; do
    if netstat -tln 2>/dev/null | grep -q ":$port "; then
        echo "   ✅ Port $port is listening"
    else
        echo "   ❌ Port $port is NOT listening"
    fi
done
echo ""

# Test local endpoints
echo "3. Testing local MCP endpoints..."
for port in 9001 9002 9003; do
    echo -n "   Port $port (/mcp): "
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
        "http://localhost:$port/mcp")
    
    if [ "$response" = "200" ]; then
        echo "✅ $response"
    else
        echo "❌ $response"
    fi
done
echo ""

# Check ngrok
echo "4. Checking ngrok status..."
if curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | grep -q "tunnels"; then
    echo "   ✅ ngrok is running"
    echo ""
    echo "   Active tunnels:"
    curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
for tunnel in data.get('tunnels', []):
    name = tunnel.get('name', 'unknown')
    public_url = tunnel.get('public_url', 'unknown')
    config = tunnel.get('config', {})
    addr = config.get('addr', 'unknown')
    print(f'      {name}: {public_url} -> {addr}')
" 2>/dev/null || echo "      (Could not parse tunnel info)"
else
    echo "   ⚠️  ngrok is NOT running or not accessible"
    echo "   Start ngrok: ngrok http 9001"
fi
echo ""

# Instructions
echo "======================================"
echo "📋 Next Steps:"
echo ""
echo "If all local tests pass (✅):"
echo "  1. Make sure ngrok is running for each port"
echo "  2. Get your ngrok URLs from the ngrok dashboard"
echo "  3. Add '/mcp' to the end of each URL"
echo "  4. Use the full URL in Prompt Opinion"
echo ""
echo "Example:"
echo "  ngrok URL: https://abc123.ngrok.io"
echo "  Prompt Opinion URL: https://abc123.ngrok.io/mcp"
echo ""
echo "Test your ngrok URLs:"
echo "  bash test-ngrok-urls.sh https://your-ngrok-url.ngrok.io"
echo ""
