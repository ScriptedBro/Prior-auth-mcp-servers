#!/usr/bin/env python3
"""
Document Generation MCP Server
Drafts prior authorization requests and appeal letters from structured context.
Supports both stdio and streamable HTTP transports.
"""

import json
import os
from typing import Any

from mcp.server import FastMCP


def _server() -> FastMCP:
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "9003")))
    path = os.getenv("MCP_PATH", "/mcp")
    
    server = FastMCP("document-generation-mcp", host=host, port=port, streamable_http_path=path)

    # PromptOpinion checks initialize -> capabilities.extensions.
    fhir_extension = {"ai.promptopinion/fhir-context": {"scopes": []}}
    original_create_init_options = server._mcp_server.create_initialization_options

    def _create_initialization_options_with_extensions(*args: Any, **kwargs: Any):
        options = original_create_init_options(*args, **kwargs)
        capabilities_dict = options.capabilities.model_dump(exclude_none=True)

        extensions = capabilities_dict.get("extensions", {})
        extensions.update(fhir_extension)
        capabilities_dict["extensions"] = extensions

        experimental = capabilities_dict.get("experimental", {})
        experimental.update(fhir_extension)
        capabilities_dict["experimental"] = experimental

        options.capabilities = options.capabilities.__class__.model_validate(capabilities_dict)
        return options

    server._mcp_server.create_initialization_options = _create_initialization_options_with_extensions

    return server


mcp = _server()


def _patient_name(patient_summary: dict[str, Any]) -> str:
    patient = patient_summary.get("patient", patient_summary)
    name = patient.get("name", {})
    family = name.get("family", "")
    given = " ".join(name.get("given", [])) if isinstance(name.get("given"), list) else ""
    return " ".join(part for part in [given, family] if part).strip() or "Unknown Patient"


def _diagnosis_lines(patient_summary: dict[str, Any]) -> list[str]:
    diagnoses = []
    for condition in patient_summary.get("active_conditions", []):
        display = condition.get("display") or condition.get("code", {}).get("text") or "Unspecified condition"
        codes = condition.get("codes", []) or condition.get("code", {}).get("coding", [])
        code_strings = [coding.get("code") for coding in codes if coding.get("code")]
        diagnoses.append(f"{display} ({', '.join(code_strings[:3])})" if code_strings else display)
    return diagnoses[:6]


def _medication_lines(patient_summary: dict[str, Any]) -> list[str]:
    medications = patient_summary.get("current_medications") or patient_summary.get("medications") or []
    lines = []
    for med in medications[:6]:
        display = med.get("display") or med.get("medication", {}).get("text") or "Unspecified medication"
        status = med.get("status")
        lines.append(f"{display}{f' [{status}]' if status else ''}")
    return lines


def _procedure_lines(patient_summary: dict[str, Any]) -> list[str]:
    procedures = patient_summary.get("recent_procedures") or patient_summary.get("procedures") or []
    lines = []
    for procedure in procedures[:6]:
        display = procedure.get("display") or procedure.get("code", {}).get("text") or "Unspecified procedure"
        date = procedure.get("date") or procedure.get("performedDateTime")
        lines.append(f"{display}{f' ({date})' if date else ''}")
    return lines


def _criteria_lines(payer_requirements: dict[str, Any]) -> list[str]:
    details = payer_requirements.get("authorization_details", payer_requirements)
    return [str(item) for item in details.get("criteria", [])[:8]]


def _build_clinical_justification(
    patient_summary: dict[str, Any],
    order_details: dict[str, Any],
    payer_requirements: dict[str, Any],
    additional_notes: str = "",
) -> str:
    patient_name = _patient_name(patient_summary)
    procedure = order_details.get("procedure_or_medication", "requested service")
    indication = order_details.get("clinical_indication") or "documented clinical need"
    diagnoses = _diagnosis_lines(patient_summary)
    medications = _medication_lines(patient_summary)
    criteria = _criteria_lines(payer_requirements)
    parts = [f"{patient_name} is being referred for {procedure} due to {indication}."]
    if diagnoses:
        parts.append(f"Relevant active diagnoses include: {'; '.join(diagnoses[:3])}.")
    if medications:
        parts.append(f"Recent or current treatments include: {'; '.join(medications[:3])}.")
    if criteria:
        parts.append(f"The request addresses payer requirements including: {'; '.join(criteria[:3])}.")
    parts.append(
        f"Based on the documented symptoms, treatment history, and current clinical picture, {procedure} is medically necessary at this time."
    )
    if additional_notes:
        parts.append(additional_notes.strip())
    return " ".join(parts)


@mcp.tool()
async def generate_clinical_justification(
    patient_summary: dict[str, Any],
    order_details: dict[str, Any],
    payer_requirements: dict[str, Any],
    additional_notes: str = "",
) -> dict[str, Any]:
    """Generate a clinical justification narrative for a prior authorization request."""
    return {
        "clinical_justification": _build_clinical_justification(
            patient_summary, order_details, payer_requirements, additional_notes
        ),
        "patient_name": _patient_name(patient_summary),
        "procedure_or_medication": order_details.get("procedure_or_medication"),
    }


@mcp.tool()
async def draft_prior_auth_request(
    payer: str,
    order_details: dict[str, Any],
    patient_summary: dict[str, Any],
    payer_requirements: dict[str, Any],
    additional_notes: str = "",
) -> dict[str, Any]:
    """Draft a structured prior authorization packet."""
    clinical_justification = _build_clinical_justification(
        patient_summary, order_details, payer_requirements, additional_notes
    )
    diagnoses = _diagnosis_lines(patient_summary)
    medications = _medication_lines(patient_summary)
    procedures = _procedure_lines(patient_summary)
    patient = patient_summary.get("patient", {})
    return {
        "payer": payer,
        "patient": {
            "id": patient.get("id"),
            "name": _patient_name(patient_summary),
            "birthDate": patient.get("birthDate"),
            "gender": patient.get("gender"),
        },
        "order": order_details,
        "diagnosis_codes": diagnoses,
        "payer_criteria_matched": _criteria_lines(payer_requirements),
        "recent_treatments": medications,
        "recent_procedures": procedures,
        "clinical_justification": clinical_justification,
        "submission_notes": additional_notes.strip(),
        "draft_document": (
            "PRIOR AUTHORIZATION REQUEST\n\n"
            f"Payer: {payer}\n"
            f"Patient: {_patient_name(patient_summary)}\n"
            f"Requested Service: {order_details.get('procedure_or_medication', 'Unknown')}\n"
            f"Clinical Indication: {order_details.get('clinical_indication', 'Not provided')}\n\n"
            "Medical Necessity:\n"
            f"{clinical_justification}\n\n"
            "Supporting Diagnoses:\n- " + ("\n- ".join(diagnoses) if diagnoses else "No diagnoses available") + "\n\n"
            "Supporting Treatment History:\n- " + ("\n- ".join(medications) if medications else "No medications available")
        ),
    }


@mcp.tool()
async def draft_appeal_letter(
    payer: str,
    procedure_or_medication: str,
    denial_reason: str,
    patient_summary: dict[str, Any],
    payer_requirements: dict[str, Any] | None = None,
    additional_notes: str = "",
) -> dict[str, Any]:
    """Draft an appeal letter for a denied prior authorization request."""
    payer_requirements = payer_requirements or {}
    clinical_justification = _build_clinical_justification(
        patient_summary,
        {"procedure_or_medication": procedure_or_medication, "clinical_indication": denial_reason},
        payer_requirements,
        additional_notes,
    )
    diagnoses = _diagnosis_lines(patient_summary)
    procedures = _procedure_lines(patient_summary)
    patient_name = _patient_name(patient_summary)
    letter = f"""PRIOR AUTHORIZATION APPEAL LETTER

Date: [Current Date]
Payer: {payer}
Patient: {patient_name}
Re: Appeal for Denied Prior Authorization - {procedure_or_medication}

Dear Medical Review Team,

I am writing to appeal the denial of prior authorization for {procedure_or_medication}.

DENIAL REASON:
{denial_reason}

CLINICAL JUSTIFICATION:
{clinical_justification}

SUPPORTING DIAGNOSES:
{chr(10).join(f"- {item}" for item in diagnoses) if diagnoses else "- No diagnoses available"}

RECENT PROCEDURES / TREATMENT HISTORY:
{chr(10).join(f"- {item}" for item in procedures) if procedures else "- No recent procedures available"}

Based on the patient's documented condition, treatment history, and payer criteria, this request remains medically necessary and should be approved on reconsideration.

Sincerely,
[Clinician Name]
[Organization]
"""
    return {
        "appeal_letter": letter,
        "payer": payer,
        "procedure_or_medication": procedure_or_medication,
        "patient_name": patient_name,
    }


@mcp.tool()
async def generate_supporting_document_checklist(
    order_details: dict[str, Any],
    payer_requirements: dict[str, Any],
    patient_summary: dict[str, Any],
) -> dict[str, Any]:
    """Generate a checklist of supporting materials for a prior authorization submission."""
    checklist = [
        "Patient demographics",
        "Ordering clinician details",
        f"Order details for {order_details.get('procedure_or_medication', 'requested service')}",
        "Relevant diagnosis codes",
        "Recent treatment history",
        "Recent procedure history",
        "Clinical justification narrative",
    ]
    for item in _criteria_lines(payer_requirements):
        checklist.append(f"Payer criterion evidence: {item}")
    if patient_summary.get("recent_labs"):
        checklist.append("Recent laboratory or observation results")
    return {"checklist": checklist, "count": len(checklist)}


async def call_tool(name: str, arguments: Any) -> list[Any]:
    class _Text:
        def __init__(self, text: str):
            self.text = text

    handlers = {
        "generate_clinical_justification": lambda: generate_clinical_justification(**arguments),
        "draft_prior_auth_request": lambda: draft_prior_auth_request(**arguments),
        "draft_appeal_letter": lambda: draft_appeal_letter(**arguments),
        "generate_supporting_document_checklist": lambda: generate_supporting_document_checklist(**arguments),
    }
    if name not in handlers:
        return [_Text(json.dumps({"error": f"Unknown tool: {name}"}))]
    result = await handlers[name]()
    return [_Text(json.dumps(result, indent=2))]


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)
