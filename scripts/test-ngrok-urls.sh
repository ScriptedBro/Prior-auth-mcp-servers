#!/bin/bash
# Test ngrok URLs for MCP servers

echo "Testing ngrok URLs for MCP servers"
echo "===================================="
echo ""

if [ $# -eq 0 ]; then
    echo "Usage: $0 <ngrok-url-1> [ngrok-url-2] [ngrok-url-3]"
    echo ""
    echo "Example:"
    echo "  $0 https://abc123.ngrok.io https://def456.ngrok.io https://ghi789.ngrok.io"
    echo ""
    echo "Or test a single URL:"
    echo "  $0 https://abc123.ngrok.io"
    exit 1
fi

test_mcp_url() {
    local url=$1
    local name=$2
    
    echo "Testing: $name"
    echo "URL: $url"
    
    # Test without /mcp path
    echo -n "  Without /mcp path: "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$response" = "404" ]; then
        echo "❌ 404 (expected - need /mcp path)"
    else
        echo "✓ $response"
    fi
    
    # Test with /mcp path
    echo -n "  With /mcp path: "
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
        "$url/mcp")
    
    if [ "$response" = "200" ]; then
        echo "✅ $response (SUCCESS!)"
        
        # Get server info
        echo "  Server response:"
        curl -s \
            -H "Content-Type: application/json" \
            -H "Accept: application/json, text/event-stream" \
            -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
            "$url/mcp" | grep -o '"name":"[^"]*"' | head -1
    else
        echo "❌ $response (FAILED)"
    fi
    echo ""
}

# Test each URL provided
test_mcp_url "$1" "Server 1 (Payer Rules)"

if [ -n "$2" ]; then
    test_mcp_url "$2" "Server 2 (Patient Records)"
fi

if [ -n "$3" ]; then
    test_mcp_url "$3" "Server 3 (Document Generation)"
fi

echo "===================================="
echo "Configuration for Prompt Opinion:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "payer-rules": {'
echo "      \"url\": \"$1/mcp\""
echo '    },'
if [ -n "$2" ]; then
echo '    "patient-records": {'
echo "      \"url\": \"$2/mcp\""
echo '    },'
fi
if [ -n "$3" ]; then
echo '    "document-generation": {'
echo "      \"url\": \"$3/mcp\""
echo '    }'
fi
echo '  }'
echo '}'
