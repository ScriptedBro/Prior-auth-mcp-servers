#!/bin/bash
# System test script for Prior Authorization Autopilot.
# Uses the project venv when available and fails only on real issues.

set -u

echo "========================================="
echo "Prior Authorization Autopilot - System Test"
echo "========================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"

if [ -x "$VENV_PYTHON" ]; then
  PYTHON_BIN="$VENV_PYTHON"
else
  PYTHON_BIN="$(command -v python3 || true)"
fi

if [ -z "${PYTHON_BIN:-}" ]; then
  echo -e "${RED}✗ FAIL${NC} - Python 3 is not installed"
  exit 1
fi

echo "Test 1: Checking HAPI FHIR Server..."
if docker ps | grep -q hapi-fhir; then
  echo -e "${GREEN}✓ PASS${NC} - HAPI FHIR container is running"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - HAPI FHIR container is not running"
  echo "  Run: docker start hapi-fhir"
  ((FAIL++))
fi
echo ""

echo "Test 2: Checking FHIR Server Accessibility..."
if curl -s -f "http://localhost:8080/fhir/metadata" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ PASS${NC} - FHIR server is accessible at http://localhost:8080/fhir"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - FHIR server is not accessible"
  ((FAIL++))
fi
echo ""

echo "Test 3: Checking Patient Data..."
PATIENT_COUNT="$("$PYTHON_BIN" - <<'PY'
import json, urllib.request
with urllib.request.urlopen("http://localhost:8080/fhir/Patient?_summary=count", timeout=10) as response:
    payload = json.load(response)
print(payload.get("total", 0))
PY
)"
if [ "${PATIENT_COUNT:-0}" -gt 0 ]; then
  echo -e "${GREEN}✓ PASS${NC} - Found $PATIENT_COUNT patients in FHIR server"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - No patients found in FHIR server"
  ((FAIL++))
fi
echo ""

echo "Test 4: Checking Python Installation..."
PYTHON_VERSION="$("$PYTHON_BIN" --version 2>&1 | cut -d' ' -f2)"
echo -e "${GREEN}✓ PASS${NC} - Python $PYTHON_VERSION is installed"
((PASS++))
echo ""

echo "Test 5: Checking MCP Dependency..."
if "$PYTHON_BIN" -c "import mcp" 2>/dev/null; then
  echo -e "${GREEN}✓ PASS${NC} - MCP library is installed"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - MCP library is not available in $PYTHON_BIN"
  ((FAIL++))
fi
echo ""

echo "Test 6: Checking httpx Dependency..."
if "$PYTHON_BIN" -c "import httpx" 2>/dev/null; then
  echo -e "${GREEN}✓ PASS${NC} - httpx library is installed"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - httpx library is not available in $PYTHON_BIN"
  ((FAIL++))
fi
echo ""

echo "Test 7: Testing FHIR Patient Query..."
if curl -s -f "http://localhost:8080/fhir/Patient/64513" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ PASS${NC} - Successfully queried patient 64513"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - Could not query patient 64513"
  ((FAIL++))
fi
echo ""

echo "Test 8: Testing FHIR Condition Query..."
if curl -s -f "http://localhost:8080/fhir/Condition?patient=64513" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ PASS${NC} - Successfully queried conditions for patient 64513"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - Could not query conditions for patient 64513"
  ((FAIL++))
fi
echo ""

echo "Test 9: Checking Project Structure..."
REQUIRED_FILES=(
  "$PROJECT_ROOT/mcp-servers/payer-rules-mcp/server.py"
  "$PROJECT_ROOT/mcp-servers/patient-records-mcp/server.py"
  "$PROJECT_ROOT/mcp-servers/document-generation-mcp/server.py"
  "$PROJECT_ROOT/agent/prior-auth-agent-config.json"
  "$PROJECT_ROOT/README.md"
)
STRUCTURE_OK=true
for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo -e "${RED}✗ Missing${NC} - $file"
    STRUCTURE_OK=false
  fi
done
if [ "$STRUCTURE_OK" = true ]; then
  echo -e "${GREEN}✓ PASS${NC} - All required files present"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - Some required files are missing"
  ((FAIL++))
fi
echo ""

echo "Test 10: Fetching Sample Patient Data..."
PATIENT_FAMILY="$("$PYTHON_BIN" - <<'PY'
import json, urllib.request
with urllib.request.urlopen("http://localhost:8080/fhir/Patient/64513", timeout=10) as response:
    payload = json.load(response)
print(payload.get("name", [{}])[0].get("family", ""))
PY
)"
if [ -n "$PATIENT_FAMILY" ]; then
  echo -e "${GREEN}✓ PASS${NC} - Retrieved patient data (Family name: $PATIENT_FAMILY)"
  ((PASS++))
else
  echo -e "${RED}✗ FAIL${NC} - Could not retrieve valid patient family name"
  ((FAIL++))
fi
echo ""

echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Tests Passed: ${GREEN}$PASS${NC}"
echo -e "Tests Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}✓ All tests passed! System is ready.${NC}"
  exit 0
else
  echo -e "${YELLOW}⚠ Some tests failed. Please fix the issues above.${NC}"
  exit 1
fi
