#!/bin/bash
# Start all MCP servers in streamable HTTP mode for remote Prompt Opinion access.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

export MCP_TRANSPORT=streamable-http

FHIR_BASE_URL="${FHIR_BASE_URL:-http://localhost:8080/fhir}"

echo "Starting MCP servers in streamable HTTP mode"
echo "FHIR_BASE_URL=$FHIR_BASE_URL"
echo ""
echo "payer-rules-mcp         -> http://127.0.0.1:9001/mcp"
echo "patient-records-mcp     -> http://127.0.0.1:9002/mcp"
echo "document-generation-mcp -> http://127.0.0.1:9003/mcp"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Trap to kill all background processes on exit
trap 'kill $(jobs -p) 2>/dev/null' EXIT

(
  export MCP_PORT=9001
  python "$PROJECT_ROOT/mcp-servers/payer-rules-mcp/server.py"
) &
PAYER_PID=$!

(
  export MCP_PORT=9002
  export FHIR_BASE_URL
  python "$PROJECT_ROOT/mcp-servers/patient-records-mcp/server.py"
) &
PATIENT_PID=$!

(
  export MCP_PORT=9003
  python "$PROJECT_ROOT/mcp-servers/document-generation-mcp/server.py"
) &
DOC_PID=$!

# Give servers time to start
sleep 2

echo "✓ All servers started"
echo "  Payer Rules MCP (PID: $PAYER_PID)"
echo "  Patient Records MCP (PID: $PATIENT_PID)"
echo "  Document Generation MCP (PID: $DOC_PID)"
echo ""

wait
