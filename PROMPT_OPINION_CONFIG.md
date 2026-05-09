# Prompt Opinion Configuration Guide

All three MCP servers now declare Prompt Opinion's FHIR extension and are ready to be added.

## FHIR Extension Status

### ✅ All Servers Declare FHIR Extension

Prompt Opinion requires all MCP servers to declare the FHIR extension, even if they don't need FHIR access.

| Server | FHIR Scopes | Why |
|--------|-------------|-----|
| **Payer Rules MCP** | None (empty array) | Uses static payer rules, no patient data needed |
| **Patient Records MCP** | 5 required scopes | Needs full patient data access from FHIR |
| **Document Generation MCP** | None (empty array) | Generates documents from provided data |

## Configuration Steps

### Step 1: Ensure ngrok is Running

You need 3 ngrok tunnels (one for each server):

```bash
# Terminal 1
ngrok http 9001

# Terminal 2
ngrok http 9002

# Terminal 3
ngrok http 9003
```

Copy the ngrok URLs (example):
- Payer Rules: `https://abc123.ngrok.io`
- Patient Records: `https://def456.ngrok.io`
- Document Generation: `https://ghi789.ngrok.io`

### Step 2: Add Payer Rules MCP

**URL**: `https://abc123.ngrok.io/mcp` (don't forget `/mcp`!)

1. In Prompt Opinion, go to Configuration → MCP Servers
2. Click "Add Server"
3. Enter the URL with `/mcp` at the end
4. Click "Continue" to initialize
5. You should see: "This server supports FHIR context" ✅
6. **FHIR Scopes**: None requested (empty list)
7. Click "Save"

**Expected Result**: ✅ No error, server added successfully

### Step 3: Add Patient Records MCP

**URL**: `https://def456.ngrok.io/mcp`

1. Click "Add Server"
2. Enter the URL with `/mcp`
3. Click "Continue" to initialize
4. You should see: "This server supports FHIR context" ✅
5. **FHIR Scopes**: You'll see 5 required scopes:
   - ✅ patient/Patient.rs (required)
   - ✅ patient/Condition.rs (required)
   - ✅ patient/MedicationRequest.rs (required)
   - ✅ patient/Procedure.rs (required)
   - ✅ patient/Observation.rs (required)
6. **Check the box** to authorize FHIR context
7. Click "Save"

**Expected Result**: ✅ Server added with FHIR authorization

### Step 4: Add Document Generation MCP

**URL**: `https://ghi789.ngrok.io/mcp`

1. Click "Add Server"
2. Enter the URL with `/mcp`
3. Click "Continue" to initialize
4. You should see: "This server supports FHIR context" ✅
5. **FHIR Scopes**: None requested (empty list)
6. Click "Save"

**Expected Result**: ✅ No error, server added successfully

## Complete Configuration

After adding all three servers, your configuration should look like:

```json
{
  "mcpServers": {
    "payer-rules": {
      "url": "https://abc123.ngrok.io/mcp"
    },
    "patient-records": {
      "url": "https://def456.ngrok.io/mcp",
      "fhirContextEnabled": true
    },
    "document-generation": {
      "url": "https://ghi789.ngrok.io/mcp"
    }
  }
}
```

## Testing the Configuration

### Test 1: List Available Tools

In Prompt Opinion, you should see tools from all three servers:

**From Payer Rules MCP:**
- check_auth_requirements
- get_auth_criteria
- list_payers
- generate_appeal_template

**From Patient Records MCP:**
- get_patient_demographics
- get_patient_conditions
- get_patient_medications
- get_patient_procedures
- get_patient_observations
- search_patients
- get_prior_auth_summary

**From Document Generation MCP:**
- generate_clinical_justification
- draft_prior_auth_request
- draft_appeal_letter
- generate_supporting_document_checklist

### Test 2: Simple Tool Call

Try calling a simple tool:

**Prompt**: "List available payers"

**Expected**: Agent calls `list_payers` from Payer Rules MCP and returns:
- Blue Cross Blue Shield
- UnitedHealthcare
- Aetna

### Test 3: Patient Data Access

**Prompt**: "Get patient demographics for patient 64513"

**Expected**: Agent calls `get_patient_demographics` from Patient Records MCP and returns patient info.

**Note**: This will use your local FHIR server (http://localhost:8080/fhir) since we're testing locally. In production with Prompt Opinion's FHIR integration, it would use the FHIR context headers.

## Troubleshooting

### Error: "This MCP server does not support PromptOpinion's FHIR extension"

**Solution**: ✅ FIXED - All servers now declare the FHIR extension

### Error: 404 Not Found

**Cause**: Missing `/mcp` in the URL

**Solution**: Make sure your URL ends with `/mcp`:
- ❌ Wrong: `https://abc123.ngrok.io`
- ✅ Correct: `https://abc123.ngrok.io/mcp`

### Error: Connection Refused

**Cause**: Servers not running or ngrok not tunneling

**Solution**:
1. Check servers are running: `ps aux | grep server.py`
2. Check ngrok is running: `curl http://127.0.0.1:4040/api/tunnels`
3. Restart if needed: `bash start-mcp-http.sh`

### FHIR Scopes Not Showing for Patient Records MCP

**Cause**: Server didn't declare scopes correctly

**Solution**: 
1. Restart servers: `bash start-mcp-http.sh`
2. Test locally: `bash diagnose-404.sh`
3. Try adding the server again in Prompt Opinion

## What Each Server Does

### Payer Rules MCP (No FHIR Access Needed)
- Provides static payer authorization rules
- Checks if procedures require prior auth
- Returns payer-specific criteria
- Generates appeal letter templates

### Patient Records MCP (FHIR Access Required)
- Fetches patient demographics from FHIR
- Gets diagnosis codes (ICD-10) from conditions
- Retrieves medication history
- Gets procedure history
- Fetches lab results and vital signs
- Provides comprehensive prior auth summaries

### Document Generation MCP (No FHIR Access Needed)
- Generates clinical justification narratives
- Drafts prior authorization requests
- Creates appeal letters
- Produces supporting document checklists

## Next Steps

1. ✅ Add all three servers to Prompt Opinion
2. ✅ Authorize FHIR context for Patient Records MCP
3. ⏭️ Create your A2A agent
4. ⏭️ Test the complete prior auth workflow
5. ⏭️ Record demo video
6. ⏭️ Submit to hackathon

## Support

If you encounter issues:
1. Check server logs in the terminal where `start-mcp-http.sh` is running
2. Check ngrok dashboard at http://127.0.0.1:4040
3. Run diagnostic: `bash diagnose-404.sh`
4. Test URLs: `bash test-ngrok-urls.sh <your-urls>`

---

**All servers are now ready for Prompt Opinion!** 🎉
