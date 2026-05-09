#!/usr/bin/env python3
"""
Verify that both MCP servers expose real data and return usable payloads.
This is an inspection script, but it still fails on real errors.
"""

import asyncio
import importlib.util
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PAYER_SERVER_PATH = BASE_DIR / ".." / "mcp-servers" / "payer-rules-mcp" / "server.py"
PATIENT_SERVER_PATH = BASE_DIR / ".." / "mcp-servers" / "patient-records-mcp" / "server.py"
os.environ["FHIR_BASE_URL"] = "http://localhost:8080/fhir"

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
        raise AssertionError(payload["error"])
    return payload


async def main():
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}MCP Server Data Verification{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    payer_server = load_module("payer_rules_server_verify", PAYER_SERVER_PATH)
    patient_server = load_module("patient_records_server_verify", PATIENT_SERVER_PATH)

    print(f"{BLUE}1. Payer Rules Data{NC}\n")
    payers = parse_result(await payer_server.call_tool("list_payers", {}))
    print(f"   Payers count: {payers['count']}")
    for payer in payers["payers"]:
        print(f"   - {payer}")
    if payers["count"] != 3:
        raise AssertionError(f"Expected 3 payers, got {payers['count']}")
    print(f"\n   {GREEN}✓ Payer list verified{NC}\n")

    print(f"{BLUE}2. BCBS MRI Rule{NC}\n")
    mri_rule = parse_result(
        await payer_server.call_tool(
            "get_auth_criteria",
            {"payer": "Blue Cross Blue Shield", "procedure_or_medication": "MRI"},
        )
    )
    details = mri_rule["authorization_details"]
    print(f"   Requires auth: {details['requires_auth']}")
    print(f"   Turnaround: {details['turnaround_time_hours']} hours")
    print(f"   Criteria count: {len(details['criteria'])}")
    if details["requires_auth"] is not True:
        raise AssertionError("BCBS MRI should require authorization")
    print(f"\n   {GREEN}✓ MRI rule verified{NC}\n")

    print(f"{BLUE}3. Patient 64513 Summary{NC}\n")
    summary = parse_result(await patient_server.call_tool("get_prior_auth_summary", {"patient_id": "64513"}))
    print(f"   Patient ID: {summary['patient']['id']}")
    print(f"   Family name: {summary['patient']['name']['family']}")
    print(f"   Active conditions: {len(summary['active_conditions'])}")
    print(f"   Current medications: {len(summary['current_medications'])}")
    print(f"   Recent procedures: {len(summary['recent_procedures'])}")
    print(f"   Recent labs: {len(summary['recent_labs'])}")
    if summary["patient"]["id"] != "64513":
        raise AssertionError("Patient summary returned wrong patient")
    print(f"\n   {GREEN}✓ Patient summary verified{NC}\n")

    print(f"{BLUE}4. Patient Search{NC}\n")
    search = parse_result(await patient_server.call_tool("search_patients", {"family_name": "Considine820"}))
    print(f"   Matches: {search['count']}")
    if not any(patient["id"] == "64513" for patient in search["patients"]):
        raise AssertionError("Expected patient 64513 in search results")
    print(f"\n   {GREEN}✓ Patient search verified{NC}\n")

    print(f"{GREEN}✓ All MCP data verification checks passed{NC}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:
        print(f"\n{RED}✗ FAIL: {exc}{NC}")
        raise SystemExit(1)
