# Document Generation MCP Server

An MCP server dedicated to drafting prior authorization packets, clinical justifications, and appeal letters.

## Features

- **Generate Clinical Justification**: Summarize why the requested service is medically necessary
- **Draft Prior Auth Request**: Produce a structured prior authorization packet from patient and payer context
- **Draft Appeal Letter**: Produce a denial appeal letter with patient-specific evidence
- **Checklist Support**: Generate a supporting documentation checklist for submission review

## Installation

```bash
uv pip install -e .
# or
pip install -e .
```

## Configuration for Prompt Opinion

For remote or hosted clients, run this server in streamable HTTP mode:

```bash
MCP_TRANSPORT=streamable-http MCP_PORT=9003 python server.py
```

This exposes the MCP endpoint at `http://127.0.0.1:9003/mcp`.

If you are tunneling with `ngrok`, expose port `9003` and use the public HTTPS URL.

```json
{
  "mcpServers": {
    "document-generation": {
      "command": "python",
      "args": ["/path/to/document-generation-mcp/server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

## Tools

- `generate_clinical_justification`
- `draft_prior_auth_request`
- `draft_appeal_letter`
- `generate_supporting_document_checklist`

## Intended Workflow

This server is designed to sit behind a dedicated Document Generation Agent in Prompt Opinion.
That agent can receive patient summaries from `patient-records-mcp` and payer criteria from
`payer-rules-mcp`, then use this MCP server to produce final documents.
