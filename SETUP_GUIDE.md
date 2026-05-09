# Setup Guide - Prior Authorization Autopilot Agent

Complete step-by-step guide to set up and test the Prior Authorization Autopilot Agent for the Agents Assemble hackathon.

## Prerequisites Checklist

- [ ] Python 3.10 or higher installed
- [ ] Docker installed and running
- [ ] HAPI FHIR server running (container: `hapi-fhir`)
- [ ] Prompt Opinion account created
- [ ] `uv` or `pip` for Python package management
- [ ] Git (for cloning/managing code)

## Step 1: Verify FHIR Server

Your HAPI FHIR server should already be running with patient data loaded.

```bash
# Check if Docker container is running
docker ps | grep hapi-fhir

# Verify patient data is loaded (should show 39 patients)
curl -s "http://localhost:8080/fhir/Patient?_summary=count" | grep total

# Test a patient query
curl "http://localhost:8080/fhir/Patient/64513" | head -50
```

**Expected Output**: 
- Docker container `hapi-fhir` is running
- Total patients: 39
- Patient data returns successfully

## Step 2: Install MCP Servers

### Option A: Using uv (Recommended)

```bash
# Install uv if not already installed
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Payer Rules MCP
cd prior-auth-agent/mcp-servers/payer-rules-mcp
uv pip install -e .

# Install Patient Records MCP
cd ../patient-records-mcp
uv pip install -e .
```

### Option B: Using pip

```bash
# Install Payer Rules MCP
cd prior-auth-agent/mcp-servers/payer-rules-mcp
pip install -e .

# Install Patient Records MCP
cd ../patient-records-mcp
pip install -e .
```

### Verify Installation

```bash
# Test Payer Rules MCP
cd prior-auth-agent/mcp-servers/payer-rules-mcp
python server.py
# Press Ctrl+C to stop

# Test Patient Records MCP
cd ../patient-records-mcp
export FHIR_BASE_URL="http://localhost:8080/fhir"
python server.py
# Press Ctrl+C to stop
```

## Step 3: Configure Prompt Opinion

### 3.1 Create/Edit MCP Configuration

Find your Prompt Opinion MCP configuration file:
- **User-level**: `~/.kiro/settings/mcp.json`
- **Workspace-level**: `.kiro/settings/mcp.json`

### 3.2 Add MCP Servers

Add the following to your `mcp.json`:

```json
{
  "mcpServers": {
    "payer-rules": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/prior-auth-agent/mcp-servers/payer-rules-mcp/server.py"],
      "disabled": false,
      "autoApprove": []
    },
    "patient-records": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/prior-auth-agent/mcp-servers/patient-records-mcp/server.py"],
      "env": {
        "FHIR_BASE_URL": "http://localhost:8080/fhir"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Important**: Replace `/ABSOLUTE/PATH/TO/` with the actual absolute path to your project directory.

To get the absolute path:
```bash
cd prior-auth-agent/mcp-servers/payer-rules-mcp
pwd
# Copy this path
```

### 3.3 Verify MCP Servers in Prompt Opinion

1. Open Prompt Opinion
2. Navigate to **MCP Server** view in the Kiro feature panel
3. You should see both `payer-rules` and `patient-records` servers
4. Check that both show as "Connected" or "Running"

## Step 4: Create the A2A Agent

### 4.1 Access Agent Builder

1. Log into [Prompt Opinion](https://promptopinion.com)
2. Navigate to **Agent Builder** or **Create New Agent**

### 4.2 Configure Agent

Use the configuration from `agent/prior-auth-agent-config.json`:

**Basic Info:**
- **Name**: Prior Authorization Autopilot
- **Version**: 1.0.0
- **Description**: Automated prior authorization agent that checks payer rules, gathers patient data, and submits authorization requests

**System Prompt:**
```
You are a Prior Authorization Autopilot Agent. Your role is to automate the prior authorization process for healthcare providers.

Your workflow:
1. Receive a clinical order (procedure, medication, or referral) with patient ID and payer information
2. Use the payer-rules-mcp to check if prior authorization is required
3. If required, fetch authorization criteria from payer-rules-mcp
4. Use patient-records-mcp to gather relevant patient data (conditions, medications, procedures, labs)
5. Match patient data against payer criteria
6. Draft a prior authorization request with:
   - Patient demographics
   - Relevant diagnosis codes (ICD-10)
   - Clinical justification
   - Supporting documentation references
   - Evidence of failed conservative treatments (if applicable)
7. If authorization is denied, use payer-rules-mcp to generate an appeal letter with clinical justification

Always:
- Be thorough in gathering clinical evidence
- Match diagnosis codes to payer requirements
- Document conservative treatment attempts
- Provide clear clinical justification
- Follow payer-specific criteria exactly
- Generate professional, evidence-based documentation

You save physicians 20+ hours per week by automating this administrative burden.
```

**MCP Servers:**
- Connect `payer-rules` MCP server
- Connect `patient-records` MCP server

### 4.3 Test Agent Configuration

Before publishing, test the agent with a simple query:
```
"List available payers"
```

Expected: Agent should use payer-rules MCP to list Blue Cross Blue Shield, UnitedHealthcare, and Aetna.

## Step 5: Test the Complete Workflow

### Test 1: Check Authorization Requirements

**Prompt:**
```
Check if Blue Cross Blue Shield requires prior authorization for MRI
```

**Expected Behavior:**
1. Agent calls `payer-rules` MCP → `check_auth_requirements`
2. Returns: Yes, requires prior auth, 48-hour turnaround

### Test 2: Get Patient Summary

**Prompt:**
```
Get a prior authorization summary for patient 64513
```

**Expected Behavior:**
1. Agent calls `patient-records` MCP → `get_prior_auth_summary`
2. Returns patient demographics, conditions, medications, procedures, labs

### Test 3: Complete Prior Auth Request

**Prompt:**
```
Submit prior authorization for MRI lumbar spine for patient 64513, insurance Blue Cross Blue Shield
```

**Expected Behavior:**
1. Checks BCBS requires prior auth for MRI ✓
2. Gets BCBS authorization criteria
3. Fetches patient 64513 comprehensive summary
4. Matches patient data to criteria
5. Drafts complete authorization request with:
   - Patient demographics
   - Diagnosis codes
   - Clinical justification
   - Conservative treatment evidence

### Test 4: Appeal Generation

**Prompt:**
```
Generate an appeal letter for denied MRI authorization for patient 64513. Denial reason: insufficient conservative treatment
```

**Expected Behavior:**
1. Gets patient comprehensive summary
2. Identifies conservative treatments in medication/procedure history
3. Generates professional appeal letter with clinical justification

## Step 6: Publish to Marketplace

### 6.1 Finalize Agent

1. Review agent configuration
2. Test all major workflows
3. Add agent metadata:
   - Tags: `prior-authorization`, `fhir`, `healthcare`, `automation`
   - Category: Healthcare Workflow Automation
   - Use Case: Prior Authorization

### 6.2 Publish

1. Click **Publish to Marketplace**
2. Fill in marketplace listing:
   - Title: Prior Authorization Autopilot
   - Short description: Automate prior authorization requests and appeals
   - Long description: Use content from README.md
   - Screenshots/Demo: Include workflow examples

### 6.3 Verify Publication

1. Search for your agent in Prompt Opinion Marketplace
2. Verify it's discoverable and invokable
3. Test invoking it from marketplace

## Step 7: Create Demo Video

### Video Structure (Under 3 minutes)

**Intro (15 seconds)**
- Problem: Prior auth takes 20+ hours/week
- Solution: AI agent automates the entire process

**Demo (2 minutes)**
1. Show agent receiving prior auth request
2. Agent checks payer rules (MCP call)
3. Agent gathers patient data (MCP call)
4. Agent drafts complete authorization request
5. Show appeal generation for denial

**Impact (30 seconds)**
- Time savings: 20 hours/week
- Faster approvals: 48-72 hours
- Reduced denials: 50%
- ROI: $100K+/year per physician

**Outro (15 seconds)**
- Built with MCP, A2A, FHIR
- Available in Prompt Opinion Marketplace

### Recording Tips

- Use screen recording software (OBS, Loom, etc.)
- Show Prompt Opinion interface
- Demonstrate actual MCP tool calls
- Show real FHIR data being queried
- Keep it fast-paced and focused

## Troubleshooting

### MCP Server Not Connecting

**Issue**: MCP server shows as "Disconnected" in Prompt Opinion

**Solutions**:
1. Verify absolute paths in `mcp.json`
2. Check Python is in PATH: `which python`
3. Test server manually: `python server.py`
4. Check logs in Prompt Opinion MCP panel
5. Restart Prompt Opinion

### FHIR Server Not Responding

**Issue**: Patient queries return errors

**Solutions**:
1. Verify Docker container is running: `docker ps`
2. Check FHIR server URL: `curl http://localhost:8080/fhir/metadata`
3. Restart HAPI FHIR container: `docker restart hapi-fhir`
4. Verify patient data loaded: `curl http://localhost:8080/fhir/Patient?_summary=count`

### Agent Not Using MCP Tools

**Issue**: Agent responds but doesn't call MCP tools

**Solutions**:
1. Verify MCP servers are connected in agent configuration
2. Check system prompt includes instructions to use tools
3. Test MCP tools directly in Prompt Opinion
4. Review agent logs for errors

### Python Dependencies Missing

**Issue**: `ModuleNotFoundError` when running MCP servers

**Solutions**:
```bash
# Reinstall dependencies
cd mcp-servers/payer-rules-mcp
pip install -e . --force-reinstall

cd ../patient-records-mcp
pip install -e . --force-reinstall

# Or use uv
uv pip install -e . --reinstall
```

## Next Steps

1. ✅ Complete setup and testing
2. ✅ Record demo video
3. ✅ Publish agent to marketplace
4. ✅ Submit to hackathon on Devpost
5. ✅ Share with community

## Support

- **Hackathon**: [Agents Assemble Devpost](https://agents-assemble.devpost.com/)
- **Prompt Opinion Docs**: [Documentation](https://promptopinion.com/docs)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)
- **FHIR**: [FHIR R4 Spec](https://hl7.org/fhir/R4/)

## Submission Checklist

- [ ] Both MCP servers installed and tested
- [ ] FHIR server running with 39 patients
- [ ] Agent created and configured in Prompt Opinion
- [ ] All test scenarios working
- [ ] Agent published to marketplace
- [ ] Demo video recorded (under 3 minutes)
- [ ] README.md completed
- [ ] Code pushed to GitHub
- [ ] Devpost submission completed

---

**Good luck with your hackathon submission! 🚀**
