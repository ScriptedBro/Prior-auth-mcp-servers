# Payer Rules MCP Server

An MCP server that provides payer-specific prior authorization rules and criteria.

## Features

- **Check Authorization Requirements**: Determine if a procedure/medication requires prior auth
- **Get Authorization Criteria**: Retrieve detailed criteria for specific payers and procedures
- **List Payers**: View all available insurance payers
- **Generate Appeal Templates**: Create appeal letters for denied authorizations

## Supported Payers

- Blue Cross Blue Shield
- UnitedHealthcare
- Aetna

## Supported Procedures/Medications

- MRI
- CT Scan
- Specialist Referrals (Cardiology, Orthopedics)
- Medications (Humira/adalimumab)

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Usage

This MCP server is designed to be used with MCP-compatible clients like Prompt Opinion.

### Configuration for Prompt Opinion

For remote or hosted clients, run this server in streamable HTTP mode:

```bash
MCP_TRANSPORT=streamable-http MCP_PORT=9001 python server.py
```

This exposes the MCP endpoint at `http://127.0.0.1:9001/mcp`.

If you are tunneling with `ngrok`, expose port `9001` and use the public HTTPS URL.

For local process-hosted clients, add to your `mcp.json`:

```json
{
  "mcpServers": {
    "payer-rules": {
      "command": "python",
      "args": ["/path/to/payer-rules-mcp/server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

## Tools

### check_auth_requirements
Check if prior authorization is required.

**Parameters:**
- `payer` (string): Insurance payer name
- `procedure_or_medication` (string): Procedure or medication name

### get_auth_criteria
Get detailed authorization criteria.

**Parameters:**
- `payer` (string): Insurance payer name
- `procedure_or_medication` (string): Procedure or medication name

### list_payers
List all available payers (no parameters required).

### generate_appeal_template
Generate an appeal letter template.

**Parameters:**
- `payer` (string): Insurance payer name
- `procedure_or_medication` (string): Denied procedure/medication
- `denial_reason` (string): Reason for denial
- `patient_context` (string, optional): Clinical context

## Example Usage

```python
# Check if MRI requires auth for BCBS
{
  "payer": "Blue Cross Blue Shield",
  "procedure_or_medication": "MRI"
}

# Get detailed criteria
{
  "payer": "Blue Cross Blue Shield",
  "procedure_or_medication": "Humira (adalimumab)"
}
```

## License

MIT
