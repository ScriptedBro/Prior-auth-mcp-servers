# Prompt Opinion FHIR Extension Implementation

This document explains how the MCP servers implement Prompt Opinion's FHIR context extension.

## What is the FHIR Extension?

Prompt Opinion's FHIR extension allows MCP servers to:
1. Declare that they need access to FHIR patient data
2. Request specific SMART scopes (permissions)
3. Receive FHIR context via HTTP headers when tools are called

## Implementation Status

### Patient Records MCP ✅ FHIR Extension Enabled

**File**: `mcp-servers/patient-records-mcp/server.py`

**Declared Scopes**:
- `patient/Patient.rs` (required) - Read and search patient demographics
- `patient/Condition.rs` (required) - Read and search conditions/diagnoses
- `patient/MedicationRequest.rs` (required) - Read and search medications
- `patient/Procedure.rs` (required) - Read and search procedures
- `patient/Observation.rs` (required) - Read and search labs/vitals

**Implementation**:
```python
server._extra_capabilities["extensions"] = {
    "ai.promptopinion/fhir-context": {
        "scopes": [
            {"name": "patient/Patient.rs", "required": True},
            {"name": "patient/Condition.rs", "required": True},
            {"name": "patient/MedicationRequest.rs", "required": True},
            {"name": "patient/Procedure.rs", "required": True},
            {"name": "patient/Observation.rs", "required": True},
        ]
    }
}
```

### Payer Rules MCP ❌ No FHIR Extension

**File**: `mcp-servers/payer-rules-mcp/server.py`

**Why**: This server uses static payer authorization rules and doesn't need access to patient data from FHIR.

### Document Generation MCP ❌ No FHIR Extension

**File**: `mcp-servers/document-generation-mcp/server.py`

**Why**: This server generates documents from data provided by other servers and doesn't directly access FHIR.

## How It Works

### 1. Server Declaration

When Prompt Opinion sends an `initialize` request to the Patient Records MCP server, the server responds with capabilities including the FHIR extension:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "capabilities": {
      "extensions": {
        "ai.promptopinion/fhir-context": {
          "scopes": [
            {"name": "patient/Patient.rs", "required": true},
            {"name": "patient/Condition.rs", "required": true},
            ...
          ]
        }
      }
    }
  }
}
```

### 2. User Authorization

In Prompt Opinion's MCP configuration UI:
1. User clicks "Continue" to initialize the server
2. Prompt Opinion reads the FHIR extension from the response
3. UI shows the requested scopes
4. User can authorize or deny FHIR context

### 3. FHIR Context Headers

When a tool is called on the Patient Records MCP server, Prompt Opinion sends these headers:

- `X-FHIR-Server-URL`: The FHIR server URL
- `X-FHIR-Access-Token`: OAuth token for FHIR access
- `X-Patient-ID`: The current patient's ID

### 4. Tool Usage

The MCP server tools can then use these headers to access FHIR data:

```python
@mcp.tool()
async def get_patient_demographics(patient_id: str):
    # In production, read from request headers:
    # fhir_url = request.headers.get("X-FHIR-Server-URL")
    # token = request.headers.get("X-FHIR-Access-Token")
    # patient_id = request.headers.get("X-Patient-ID")
    
    # For now, using environment variables for local testing
    fhir_url = FHIR_BASE_URL
    ...
```

## Testing

### Local Testing (Without Prompt Opinion)

When testing locally, the servers use:
- `FHIR_BASE_URL` environment variable
- No authentication (open HAPI FHIR server)
- Patient ID passed as tool parameter

```bash
# Start servers
bash start-mcp-http.sh

# Test locally
curl http://localhost:9002/mcp ...
```

### Production (With Prompt Opinion)

When deployed with Prompt Opinion:
- FHIR URL comes from `X-FHIR-Server-URL` header
- Authentication via `X-FHIR-Access-Token` header
- Patient ID from `X-Patient-ID` header

## Configuration in Prompt Opinion

### Step 1: Add MCP Server

In Prompt Opinion Configuration → MCP Servers:

```json
{
  "mcpServers": {
    "patient-records": {
      "url": "https://your-ngrok-url.ngrok.io/mcp"
    }
  }
}
```

### Step 2: Click "Continue"

This sends an `initialize` request and reads the FHIR extension.

### Step 3: Authorize Scopes

You'll see a checkbox to enable FHIR context and a list of requested scopes:
- ✅ patient/Patient.rs (required)
- ✅ patient/Condition.rs (required)
- ✅ patient/MedicationRequest.rs (required)
- ✅ patient/Procedure.rs (required)
- ✅ patient/Observation.rs (required)

Check the box to authorize.

### Step 4: Save Configuration

The server is now configured and will receive FHIR context headers.

## SMART Scopes Explained

| Scope | Meaning | Why We Need It |
|-------|---------|----------------|
| `patient/Patient.rs` | Read and Search Patient | Get demographics for prior auth |
| `patient/Condition.rs` | Read and Search Conditions | Get diagnosis codes (ICD-10) |
| `patient/MedicationRequest.rs` | Read and Search Medications | Check conservative treatments |
| `patient/Procedure.rs` | Read and Search Procedures | Verify treatment history |
| `patient/Observation.rs` | Read and Search Observations | Get lab results |

The `.rs` suffix means "read" and "search" permissions.

## Security Considerations

### Required vs Optional Scopes

All our scopes are marked as `required: true` because:
- The server cannot function without access to patient data
- Prior authorization requires complete patient context
- Users must consent to all scopes or not use the server

### Token Handling

- Tokens are passed via headers (not stored)
- Tokens are used only for the duration of the tool call
- No offline access requested (no `offline_access` scope)

### Data Privacy

- Server only accesses data when tools are called
- No background processing
- No data storage
- FHIR access is scoped to current patient only

## Troubleshooting

### "This MCP server does not support PromptOpinion's FHIR extension"

**Cause**: The server didn't include the FHIR extension in its initialize response.

**Solution**: 
1. Verify the server code includes the extension declaration
2. Restart the server
3. Click "Continue" again in Prompt Opinion to re-initialize

### Scopes Not Showing

**Cause**: The extension format is incorrect.

**Solution**: Check that the extension follows this exact structure:
```json
{
  "ai.promptopinion/fhir-context": {
    "scopes": [
      {"name": "patient/Patient.rs", "required": true}
    ]
  }
}
```

### 401 Unauthorized from FHIR Server

**Cause**: Token is invalid or expired.

**Solution**: This is handled by Prompt Opinion. If it persists, check:
1. FHIR server is accessible
2. OAuth configuration is correct
3. Token hasn't expired

## Next Steps

1. ✅ FHIR extension implemented
2. ⏭️ Test with Prompt Opinion
3. ⏭️ Verify scopes are displayed correctly
4. ⏭️ Authorize FHIR context
5. ⏭️ Test tools with real FHIR data

## References

- [Prompt Opinion FHIR Context Docs](https://docs.promptopinion.ai/fhir-context/mcp-fhir-context)
- [SMART on FHIR Scopes](http://hl7.org/fhir/smart-app-launch/scopes-and-launch-context.html)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
