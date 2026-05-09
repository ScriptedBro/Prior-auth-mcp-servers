#!/usr/bin/env python3
"""
End-to-end MCP protocol tests using the installed MCP stdio client.
This validates that the servers work through the actual MCP transport,
not just by importing Python functions directly.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import urllib.request

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

BASE_DIR = Path(__file__).resolve().parent
PAYER_SERVER_PATH = BASE_DIR / ".." / "mcp-servers" / "payer-rules-mcp" / "server.py"
PATIENT_SERVER_PATH = BASE_DIR / ".." / "mcp-servers" / "patient-records-mcp" / "server.py"
DOCUMENT_SERVER_PATH = BASE_DIR / ".." / "mcp-servers" / "document-generation-mcp" / "server.py"
FHIR_BASE_URL = "http://localhost:8080/fhir"

GREEN = "\033[0;32m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def expect(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def parse_content(result):
    expect(result.isError is False, "MCP tool call returned isError=true")
    expect(result.content, "MCP tool call returned no content")
    first = result.content[0]
    text = getattr(first, "text", None)
    expect(text is not None, "First MCP content block was not text")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict) and payload.get("error"):
        raise AssertionError(f"Server returned error payload: {payload['error']}")
    return payload


def live_patient_id() -> str:
    with urllib.request.urlopen(f"{FHIR_BASE_URL}/Patient?_count=1", timeout=10) as response:
        payload = json.load(response)
    entries = payload.get("entry", [])
    expect(bool(entries), "Expected at least one patient in the FHIR server")
    return entries[0]["resource"]["id"]


async def with_session(server_path: Path):
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        env={**os.environ, "FHIR_BASE_URL": FHIR_BASE_URL, "MCP_TRANSPORT": "stdio"},
        cwd=str(BASE_DIR),
    )
    return stdio_client(params)


async def test_payer_rules():
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Testing Payer Rules MCP via MCP Protocol{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    async with await with_session(PAYER_SERVER_PATH) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            print(f"{YELLOW}Test 1: List Tools{NC}")
            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            expect(
                tool_names == {
                    "check_auth_requirements",
                    "get_auth_criteria",
                    "list_payers",
                    "generate_appeal_template",
                },
                f"Unexpected tool set: {sorted(tool_names)}",
            )
            print(f"  Tools found: {len(tool_names)}")
            print(f"  {GREEN}✓ PASS{NC}\n")

            print(f"{YELLOW}Test 2: list_payers{NC}")
            data = parse_content(await session.call_tool("list_payers"))
            expect(data["count"] == 3, f"Expected 3 payers, got {data['count']}")
            print(f"  Payers found: {data['count']}")
            print(f"  {GREEN}✓ PASS{NC}\n")

            print(f"{YELLOW}Test 3: check_auth_requirements{NC}")
            data = parse_content(
                await session.call_tool(
                    "check_auth_requirements",
                    {"payer": "Blue Cross Blue Shield", "procedure_or_medication": "MRI"},
                )
            )
            expect(data["requires_prior_authorization"] is True, "MRI should require auth")
            expect(data["turnaround_time_hours"] == 48, "Expected 48 hour turnaround")
            print(f"  Requires auth: {data['requires_prior_authorization']}")
            print(f"  Turnaround: {data['turnaround_time_hours']} hours")
            print(f"  {GREEN}✓ PASS{NC}\n")


async def test_patient_records():
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Testing Patient Records MCP via MCP Protocol{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    patient_id = live_patient_id()

    async with await with_session(PATIENT_SERVER_PATH) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            print(f"{YELLOW}Test 1: List Tools{NC}")
            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            expected = {
                "get_patient_demographics",
                "get_patient_conditions",
                "get_patient_medications",
                "get_patient_procedures",
                "get_patient_observations",
                "search_patients",
                "get_prior_auth_summary",
            }
            expect(tool_names == expected, f"Unexpected tool set: {sorted(tool_names)}")
            print(f"  Tools found: {len(tool_names)}")
            print(f"  {GREEN}✓ PASS{NC}\n")

            print(f"{YELLOW}Test 2: get_patient_demographics{NC}")
            demographics = parse_content(await session.call_tool("get_patient_demographics", {"patient_id": patient_id}))
            expect(demographics["id"] == patient_id, "Patient id mismatch")
            expect(demographics["name"]["family"], "Expected family name")
            print(f"  Patient ID: {demographics['id']}")
            print(f"  Family name: {demographics['name']['family']}")
            print(f"  {GREEN}✓ PASS{NC}\n")

            print(f"{YELLOW}Test 3: search_patients{NC}")
            data = parse_content(await session.call_tool("search_patients", {"family_name": demographics["name"]["family"]}))
            expect(data["count"] >= 1, "Expected at least one search result")
            expect(any(p["id"] == patient_id for p in data["patients"]), "Expected patient in results")
            print(f"  Matches found: {data['count']}")
            print(f"  {GREEN}✓ PASS{NC}\n")

            print(f"{YELLOW}Test 4: get_prior_auth_summary{NC}")
            summary = parse_content(await session.call_tool("get_prior_auth_summary", {"patient_id": patient_id}))
            expect(summary["patient"]["id"] == patient_id, "Summary patient mismatch")
            expect(len(summary["active_conditions"]) >= 1, "Expected active conditions")
            expect(len(summary["current_medications"]) >= 1, "Expected current medications")
            print(f"  Active conditions: {len(summary['active_conditions'])}")
            print(f"  Current medications: {len(summary['current_medications'])}")
            print(f"  Recent procedures: {len(summary['recent_procedures'])}")
            print(f"  Recent labs: {len(summary['recent_labs'])}")
            print(f"  {GREEN}✓ PASS{NC}\n")
            return patient_id, summary


async def test_document_generation():
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Testing Document Generation MCP via MCP Protocol{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    patient_id = live_patient_id()

    async with await with_session(PATIENT_SERVER_PATH) as patient_streams:
        async with ClientSession(*patient_streams) as patient_session:
            await patient_session.initialize()
            patient_summary = parse_content(await patient_session.call_tool("get_prior_auth_summary", {"patient_id": patient_id}))

    async with await with_session(PAYER_SERVER_PATH) as payer_streams:
        async with ClientSession(*payer_streams) as payer_session:
            await payer_session.initialize()
            payer_requirements = parse_content(
                await payer_session.call_tool(
                    "get_auth_criteria",
                    {"payer": "Blue Cross Blue Shield", "procedure_or_medication": "MRI"},
                )
            )

    async with await with_session(DOCUMENT_SERVER_PATH) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            print(f"{YELLOW}Test 1: List Tools{NC}")
            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            expected = {
                "generate_clinical_justification",
                "draft_prior_auth_request",
                "draft_appeal_letter",
                "generate_supporting_document_checklist",
            }
            expect(tool_names == expected, f"Unexpected tool set: {sorted(tool_names)}")
            print(f"  Tools found: {len(tool_names)}")
            print(f"  {GREEN}✓ PASS{NC}\n")

            order_details = {
                "procedure_or_medication": "MRI lumbar spine",
                "clinical_indication": "persistent low back pain with functional decline",
            }

            print(f"{YELLOW}Test 2: draft_prior_auth_request{NC}")
            data = parse_content(
                await session.call_tool(
                    "draft_prior_auth_request",
                    {
                        "payer": "Blue Cross Blue Shield",
                        "order_details": order_details,
                        "patient_summary": patient_summary,
                        "payer_requirements": payer_requirements,
                    },
                )
            )
            expect(data["patient"]["id"] == patient_id, "Expected matching patient id")
            expect("PRIOR AUTHORIZATION REQUEST" in data["draft_document"], "Expected draft request heading")
            print(f"  Packet patient ID: {data['patient']['id']}")
            print(f"  {GREEN}✓ PASS{NC}\n")

            print(f"{YELLOW}Test 3: draft_appeal_letter{NC}")
            data = parse_content(
                await session.call_tool(
                    "draft_appeal_letter",
                    {
                        "payer": "Blue Cross Blue Shield",
                        "procedure_or_medication": "MRI lumbar spine",
                        "denial_reason": "Insufficient conservative treatment documented",
                        "patient_summary": patient_summary,
                        "payer_requirements": payer_requirements,
                    },
                )
            )
            expect("PRIOR AUTHORIZATION APPEAL LETTER" in data["appeal_letter"], "Expected appeal heading")
            print(f"  Appeal patient: {data['patient_name']}")
            print(f"  {GREEN}✓ PASS{NC}\n")


async def main():
    print("\n🧪 MCP Server Protocol Test Suite")
    print("=" * 60)
    await test_payer_rules()
    await test_patient_records()
    await test_document_generation()
    print(f"\n{GREEN}✓ All MCP protocol tests passed{NC}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except AssertionError as exc:
        print(f"\n{RED}✗ FAIL: {exc}{NC}")
        raise SystemExit(1)
    except Exception as exc:
        print(f"\n{RED}✗ ERROR: {exc}{NC}")
        raise SystemExit(1)
