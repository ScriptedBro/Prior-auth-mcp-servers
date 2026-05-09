#!/usr/bin/env python3
"""
Direct tests for all MCP server implementations.
Loads each server module by file path, calls the actual tool handlers, and
asserts on real return values using live FHIR data.
"""

import asyncio
import importlib.util
import json
import os
from pathlib import Path
import urllib.request

BASE_DIR = Path(__file__).resolve().parent
PAYER_SERVER_PATH = BASE_DIR / ".." / "mcp-servers" / "payer-rules-mcp" / "server.py"
PATIENT_SERVER_PATH = BASE_DIR / ".." / "mcp-servers" / "patient-records-mcp" / "server.py"
DOCUMENT_SERVER_PATH = BASE_DIR / ".." / "mcp-servers" / "document-generation-mcp" / "server.py"
FHIR_BASE_URL = "http://localhost:8080/fhir"
os.environ["FHIR_BASE_URL"] = FHIR_BASE_URL

GREEN = "\033[0;32m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_result(result):
    if not result:
        raise AssertionError("Tool returned no content")
    text = result[0].text
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict) and payload.get("error"):
        raise AssertionError(f"Tool returned error: {payload['error']}")
    return payload


def expect(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def live_patient_id() -> str:
    with urllib.request.urlopen(f"{FHIR_BASE_URL}/Patient?_count=1", timeout=10) as response:
        payload = json.load(response)
    entries = payload.get("entry", [])
    expect(bool(entries), "Expected at least one patient in the FHIR server")
    return entries[0]["resource"]["id"]


async def test_payer_rules_mcp():
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Testing Payer Rules MCP Server{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    server = load_module("payer_rules_server_test", PAYER_SERVER_PATH)

    print(f"{YELLOW}Test 1: List Payers{NC}")
    data = parse_result(await server.call_tool("list_payers", {}))
    expect(data["count"] == 3, f"Expected 3 payers, got {data['count']}")
    expect("Blue Cross Blue Shield" in data["payers"], "BCBS missing from payer list")
    print(f"  Payers found: {data['count']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 2: Check Authorization Requirements{NC}")
    data = parse_result(
        await server.call_tool(
            "check_auth_requirements",
            {"payer": "Blue Cross Blue Shield", "procedure_or_medication": "MRI"},
        )
    )
    expect(data["requires_prior_authorization"] is True, "MRI should require authorization")
    expect(data["turnaround_time_hours"] == 48, "BCBS MRI turnaround should be 48 hours")
    print(f"  Requires auth: {data['requires_prior_authorization']}")
    print(f"  Turnaround: {data['turnaround_time_hours']} hours")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 3: Get Authorization Criteria{NC}")
    data = parse_result(
        await server.call_tool(
            "get_auth_criteria",
            {"payer": "Blue Cross Blue Shield", "procedure_or_medication": "MRI"},
        )
    )
    criteria = data["authorization_details"]["criteria"]
    expect(len(criteria) == 3, f"Expected 3 MRI criteria, got {len(criteria)}")
    expect("6+ weeks" in criteria[0], "Expected conservative treatment criterion")
    print(f"  Criteria count: {len(criteria)}")
    print(f"  First criterion: {criteria[0]}")
    print(f"  {GREEN}✓ PASS{NC}\n")


async def test_patient_records_mcp():
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Testing Patient Records MCP Server{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    server = load_module("patient_records_server_test", PATIENT_SERVER_PATH)
    patient_id = live_patient_id()

    print(f"{YELLOW}Test 1: Get Patient Demographics{NC}")
    demographics = parse_result(await server.call_tool("get_patient_demographics", {"patient_id": patient_id}))
    expect(demographics["id"] == patient_id, f"Expected patient {patient_id}, got {demographics['id']}")
    expect(demographics["name"]["family"], "Expected patient family name")
    expect(demographics["gender"] in {"male", "female", "other", "unknown"}, "Unexpected patient gender")
    print(f"  Patient ID: {demographics['id']}")
    print(f"  Family name: {demographics['name']['family']}")
    print(f"  Gender: {demographics['gender']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 2: Search Patients{NC}")
    data = parse_result(await server.call_tool("search_patients", {"family_name": demographics["name"]["family"]}))
    expect(data["count"] >= 1, "Expected at least one patient search match")
    expect(any(patient["id"] == patient_id for patient in data["patients"]), "Expected patient in search results")
    print(f"  Matches found: {data['count']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 3: Get Patient Conditions{NC}")
    data = parse_result(await server.call_tool("get_patient_conditions", {"patient_id": patient_id}))
    expect(data["count"] >= 1, "Expected patient conditions")
    first_condition = data["conditions"][0]
    expect(first_condition["id"], "Expected condition id")
    print(f"  Conditions found: {data['count']}")
    print(f"  First condition ID: {first_condition['id']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 4: Get Patient Medications{NC}")
    data = parse_result(await server.call_tool("get_patient_medications", {"patient_id": patient_id}))
    expect(data["count"] >= 1, "Expected patient medications")
    print(f"  Medications found: {data['count']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 5: Get Patient Procedures{NC}")
    data = parse_result(await server.call_tool("get_patient_procedures", {"patient_id": patient_id}))
    expect(data["count"] >= 1, "Expected patient procedures")
    print(f"  Procedures found: {data['count']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 6: Get Patient Observations{NC}")
    data = parse_result(await server.call_tool("get_patient_observations", {"patient_id": patient_id}))
    expect(data["count"] >= 1, "Expected patient observations")
    print(f"  Observations found: {data['count']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 7: Get Prior Authorization Summary{NC}")
    data = parse_result(await server.call_tool("get_prior_auth_summary", {"patient_id": patient_id}))
    expect(data["patient"]["id"] == patient_id, "Summary patient id mismatch")
    expect(len(data["active_conditions"]) >= 1, "Expected active conditions in summary")
    expect(len(data["current_medications"]) >= 1, "Expected current medications in summary")
    expect(len(data["recent_procedures"]) >= 1, "Expected recent procedures in summary")
    expect(len(data["recent_labs"]) >= 1, "Expected recent labs in summary")
    print(f"  Active conditions: {len(data['active_conditions'])}")
    print(f"  Current medications: {len(data['current_medications'])}")
    print(f"  Recent procedures: {len(data['recent_procedures'])}")
    print(f"  Recent labs: {len(data['recent_labs'])}")
    print(f"  {GREEN}✓ PASS{NC}\n")
    return patient_id, data


async def test_document_generation_mcp():
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Testing Document Generation MCP Server{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    payer_server = load_module("payer_rules_server_docgen_test", PAYER_SERVER_PATH)
    patient_server = load_module("patient_records_server_docgen_test", PATIENT_SERVER_PATH)
    document_server = load_module("document_generation_server_test", DOCUMENT_SERVER_PATH)

    patient_id = live_patient_id()
    patient_summary = parse_result(await patient_server.call_tool("get_prior_auth_summary", {"patient_id": patient_id}))
    payer_requirements = parse_result(
        await payer_server.call_tool(
            "get_auth_criteria",
            {"payer": "Blue Cross Blue Shield", "procedure_or_medication": "MRI"},
        )
    )
    order_details = {
        "procedure_or_medication": "MRI lumbar spine",
        "clinical_indication": "persistent low back pain with functional decline",
    }

    print(f"{YELLOW}Test 1: generate_clinical_justification{NC}")
    data = parse_result(
        await document_server.call_tool(
            "generate_clinical_justification",
            {
                "patient_summary": patient_summary,
                "order_details": order_details,
                "payer_requirements": payer_requirements,
            },
        )
    )
    expect("medically necessary" in data["clinical_justification"], "Expected medical necessity language")
    print(f"  Patient name: {data['patient_name']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 2: draft_prior_auth_request{NC}")
    data = parse_result(
        await document_server.call_tool(
            "draft_prior_auth_request",
            {
                "payer": "Blue Cross Blue Shield",
                "order_details": order_details,
                "patient_summary": patient_summary,
                "payer_requirements": payer_requirements,
            },
        )
    )
    expect("PRIOR AUTHORIZATION REQUEST" in data["draft_document"], "Expected prior auth request heading")
    expect(data["patient"]["id"] == patient_id, "Expected matching patient id in request packet")
    print(f"  Packet patient ID: {data['patient']['id']}")
    print(f"  {GREEN}✓ PASS{NC}\n")

    print(f"{YELLOW}Test 3: draft_appeal_letter{NC}")
    data = parse_result(
        await document_server.call_tool(
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
    expect("PRIOR AUTHORIZATION APPEAL LETTER" in data["appeal_letter"], "Expected appeal letter heading")
    print(f"  Appeal patient: {data['patient_name']}")
    print(f"  {GREEN}✓ PASS{NC}\n")


async def main():
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}MCP Server Tool Tests{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")

    await test_payer_rules_mcp()
    await test_patient_records_mcp()
    await test_document_generation_mcp()

    print(f"\n{GREEN}✓ All direct MCP tool tests passed{NC}")
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
