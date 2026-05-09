# Patient Records MCP Server

An MCP server that fetches patient data from FHIR servers for prior authorization workflows. Implements SHARP extension specs for FHIR context propagation.

## Features

- **Patient Demographics**: Fetch patient demographic information
- **Conditions**: Get patient diagnoses with ICD-10 codes
- **Medications**: Retrieve current and past medications
- **Procedures**: Access procedure history
- **Observations**: Get lab results and vital signs
- **Patient Search**: Search for patients by name or identifier
- **Prior Auth Summary**: Comprehensive patient summary for authorization requests

## SHARP Context Support

This server supports SHARP extension specs for FHIR context propagation:
- Accepts `fhir_token` parameter for authenticated FHIR access
- Propagates authorization context through multi-agent workflows
- Compatible with EHR session credentials

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Configuration

Set the FHIR server URL via environment variable:

```bash
export FHIR_BASE_URL="http://localhost:8080/fhir"
```

Default: `http://localhost:8080/fhir`

## Usage

### Configuration for Prompt Opinion

For remote or hosted clients, run this server in streamable HTTP mode:

```bash
FHIR_BASE_URL="http://localhost:8080/fhir" \
MCP_TRANSPORT=streamable-http \
MCP_PORT=9002 \
python server.py
```

This exposes the MCP endpoint at `http://127.0.0.1:9002/mcp`.

If Prompt Opinion is online, you can expose this port with `ngrok` and point the server at a
publicly reachable FHIR base URL.

Add to your `mcp.json`:

```json
{
  "mcpServers": {
    "patient-records": {
      "command": "python",
      "args": ["/path/to/patient-records-mcp/server.py"],
      "env": {
        "FHIR_BASE_URL": "http://localhost:8080/fhir",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

## Tools

### get_patient_demographics
Fetch patient demographic information.

**Parameters:**
- `patient_id` (string, required): FHIR Patient resource ID
- `fhir_token` (string, optional): Authorization token

### get_patient_conditions
Get patient's active conditions with diagnosis codes.

**Parameters:**
- `patient_id` (string, required): FHIR Patient resource ID
- `fhir_token` (string, optional): Authorization token

### get_patient_medications
Retrieve patient's medication history.

**Parameters:**
- `patient_id` (string, required): FHIR Patient resource ID
- `fhir_token` (string, optional): Authorization token

### get_patient_procedures
Get patient's procedure history.

**Parameters:**
- `patient_id` (string, required): FHIR Patient resource ID
- `fhir_token` (string, optional): Authorization token

### get_patient_observations
Fetch lab results and vital signs.

**Parameters:**
- `patient_id` (string, required): FHIR Patient resource ID
- `observation_type` (string, optional): Filter by type (e.g., 'laboratory', 'vital-signs')
- `fhir_token` (string, optional): Authorization token

### search_patients
Search for patients by criteria.

**Parameters:**
- `family_name` (string, optional): Last name
- `given_name` (string, optional): First name
- `identifier` (string, optional): Patient identifier
- `fhir_token` (string, optional): Authorization token

### get_prior_auth_summary
Get comprehensive patient summary for prior authorization.

**Parameters:**
- `patient_id` (string, required): FHIR Patient resource ID
- `fhir_token` (string, optional): Authorization token

**Returns:**
- Patient demographics
- Active conditions with ICD-10 codes
- Current medications
- Recent procedures
- Recent lab results

## Example Usage

```python
# Get patient summary for prior auth
{
  "patient_id": "123",
  "fhir_token": "optional-bearer-token"
}

# Search for a patient
{
  "family_name": "Smith",
  "given_name": "John"
}
```

## FHIR Compatibility

- FHIR R4 compliant
- Tested with HAPI FHIR server
- Supports standard FHIR search parameters

## License

MIT
