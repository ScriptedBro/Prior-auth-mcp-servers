#!/usr/bin/env python3
"""
Patient Records MCP Server
Fetches patient data from FHIR server for prior authorization requests.
Supports both stdio and streamable HTTP transports.
"""

import asyncio
import json
import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import Context, FastMCP

FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir")


def _server() -> FastMCP:
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "9002")))
    path = os.getenv("MCP_PATH", "/mcp")
    
    server = FastMCP("patient-records-mcp", host=host, port=port, streamable_http_path=path)

    # PromptOpinion checks initialize -> capabilities.extensions for this declaration.
    # FastMCP doesn't surface a first-class API for arbitrary "extensions", so we
    # patch initialization options to include it explicitly.
    fhir_extension = {
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

    original_create_init_options = server._mcp_server.create_initialization_options

    def _create_initialization_options_with_extensions(*args: Any, **kwargs: Any):
        options = original_create_init_options(*args, **kwargs)
        capabilities_dict = options.capabilities.model_dump(exclude_none=True)

        # Required for PromptOpinion FHIR extension support.
        extensions = capabilities_dict.get("extensions", {})
        extensions.update(fhir_extension)
        capabilities_dict["extensions"] = extensions

        # Also mirror in MCP experimental capabilities for broader compatibility.
        experimental = capabilities_dict.get("experimental", {})
        experimental.update(fhir_extension)
        capabilities_dict["experimental"] = experimental

        options.capabilities = options.capabilities.__class__.model_validate(capabilities_dict)
        return options

    server._mcp_server.create_initialization_options = _create_initialization_options_with_extensions

    return server


mcp = _server()


async def fetch_fhir_resource(resource_type: str, resource_id: str, fhir_token: Optional[str] = None) -> dict:
    """Fetch a FHIR resource. Uses Prompt Opinion headers if available."""
    # Try to get FHIR context from Prompt Opinion headers (via request context)
    # For now, fall back to parameters or environment
    headers = {}
    if fhir_token:
        headers["Authorization"] = f"Bearer {fhir_token}"
    
    # Use FHIR_BASE_URL from environment unless a header-derived value is passed.
    fhir_url = FHIR_BASE_URL
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{fhir_url}/{resource_type}/{resource_id}", headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def search_fhir_resources(resource_type: str, params: dict, fhir_token: Optional[str] = None) -> dict:
    """Search FHIR resources. Uses Prompt Opinion headers if available."""
    headers = {}
    if fhir_token:
        headers["Authorization"] = f"Bearer {fhir_token}"
    
    fhir_url = FHIR_BASE_URL
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{fhir_url}/{resource_type}", params=params, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()


def _error(exc: Exception) -> dict[str, Any]:
    return {"error": str(exc), "type": type(exc).__name__}


def _get_context_headers(ctx: Context | None) -> dict[str, str]:
    """Extract request headers from FastMCP request context."""
    if ctx is None:
        return {}
    try:
        request = ctx.request_context.request
        headers = getattr(request, "headers", None)
        if headers is None:
            return {}
        return {str(k).lower(): str(v) for k, v in headers.items()}
    except Exception:
        return {}


def _resolve_patient_and_token(
    patient_id: str | None,
    fhir_token: str | None,
    ctx: Context | None = None,
) -> tuple[str | None, str | None]:
    headers = _get_context_headers(ctx)
    resolved_patient_id = patient_id or headers.get("x-patient-id")
    resolved_token = fhir_token or headers.get("x-fhir-access-token")
    return resolved_patient_id, resolved_token


def _resolve_fhir_base_url(ctx: Context | None = None) -> str:
    headers = _get_context_headers(ctx)
    return headers.get("x-fhir-server-url") or FHIR_BASE_URL


async def fetch_fhir_resource_with_url(
    resource_type: str,
    resource_id: str,
    fhir_url: str,
    fhir_token: Optional[str] = None,
) -> dict:
    headers = {}
    if fhir_token:
        headers["Authorization"] = f"Bearer {fhir_token}"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{fhir_url}/{resource_type}/{resource_id}", headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def search_fhir_resources_with_url(
    resource_type: str,
    params: dict,
    fhir_url: str,
    fhir_token: Optional[str] = None,
) -> dict:
    headers = {}
    if fhir_token:
        headers["Authorization"] = f"Bearer {fhir_token}"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{fhir_url}/{resource_type}", params=params, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_patient_demographics(
    patient_id: str | None = None,
    fhir_token: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get patient demographic information from the FHIR server."""
    try:
        patient_id, fhir_token = _resolve_patient_and_token(patient_id, fhir_token, ctx)
        if not patient_id:
            return {"error": "Missing patient_id (or X-Patient-ID context header)", "type": "ValidationError"}
        fhir_url = _resolve_fhir_base_url(ctx)
        patient = await fetch_fhir_resource_with_url("Patient", patient_id, fhir_url, fhir_token)
        return {
            "id": patient.get("id"),
            "name": patient.get("name", [{}])[0],
            "gender": patient.get("gender"),
            "birthDate": patient.get("birthDate"),
            "address": patient.get("address", [{}])[0] if patient.get("address") else {},
            "telecom": patient.get("telecom", []),
        }
    except Exception as exc:
        return _error(exc)


@mcp.tool()
async def get_patient_conditions(
    patient_id: str | None = None,
    fhir_token: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get patient's active conditions and diagnoses."""
    try:
        patient_id, fhir_token = _resolve_patient_and_token(patient_id, fhir_token, ctx)
        if not patient_id:
            return {"error": "Missing patient_id (or X-Patient-ID context header)", "type": "ValidationError"}
        fhir_url = _resolve_fhir_base_url(ctx)
        bundle = await search_fhir_resources_with_url(
            "Condition", {"patient": patient_id, "_sort": "-onset-date"}, fhir_url, fhir_token
        )
        conditions = []
        for entry in bundle.get("entry", []):
            condition = entry.get("resource", {})
            conditions.append(
                {
                    "id": condition.get("id"),
                    "code": condition.get("code", {}),
                    "clinicalStatus": condition.get("clinicalStatus", {}),
                    "onsetDateTime": condition.get("onsetDateTime"),
                    "recordedDate": condition.get("recordedDate"),
                }
            )
        return {"patient_id": patient_id, "conditions": conditions, "count": len(conditions)}
    except Exception as exc:
        return _error(exc)


@mcp.tool()
async def get_patient_medications(
    patient_id: str | None = None,
    fhir_token: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get patient's current and past medications."""
    try:
        patient_id, fhir_token = _resolve_patient_and_token(patient_id, fhir_token, ctx)
        if not patient_id:
            return {"error": "Missing patient_id (or X-Patient-ID context header)", "type": "ValidationError"}
        fhir_url = _resolve_fhir_base_url(ctx)
        bundle = await search_fhir_resources_with_url(
            "MedicationRequest", {"patient": patient_id, "_sort": "-authoredon"}, fhir_url, fhir_token
        )
        medications = []
        for entry in bundle.get("entry", []):
            med = entry.get("resource", {})
            medications.append(
                {
                    "id": med.get("id"),
                    "medication": med.get("medicationCodeableConcept", {}),
                    "status": med.get("status"),
                    "authoredOn": med.get("authoredOn"),
                    "dosageInstruction": med.get("dosageInstruction", []),
                }
            )
        return {"patient_id": patient_id, "medications": medications, "count": len(medications)}
    except Exception as exc:
        return _error(exc)


@mcp.tool()
async def get_patient_procedures(
    patient_id: str | None = None,
    fhir_token: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get patient's procedure history."""
    try:
        patient_id, fhir_token = _resolve_patient_and_token(patient_id, fhir_token, ctx)
        if not patient_id:
            return {"error": "Missing patient_id (or X-Patient-ID context header)", "type": "ValidationError"}
        fhir_url = _resolve_fhir_base_url(ctx)
        bundle = await search_fhir_resources_with_url("Procedure", {"patient": patient_id, "_sort": "-date"}, fhir_url, fhir_token)
        procedures = []
        for entry in bundle.get("entry", []):
            procedure = entry.get("resource", {})
            procedures.append(
                {
                    "id": procedure.get("id"),
                    "code": procedure.get("code", {}),
                    "status": procedure.get("status"),
                    "performedDateTime": procedure.get("performedDateTime"),
                    "performedPeriod": procedure.get("performedPeriod"),
                }
            )
        return {"patient_id": patient_id, "procedures": procedures, "count": len(procedures)}
    except Exception as exc:
        return _error(exc)


@mcp.tool()
async def get_patient_observations(
    patient_id: str | None = None,
    observation_type: str | None = None,
    fhir_token: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get patient's lab results and vital signs."""
    try:
        patient_id, fhir_token = _resolve_patient_and_token(patient_id, fhir_token, ctx)
        if not patient_id:
            return {"error": "Missing patient_id (or X-Patient-ID context header)", "type": "ValidationError"}
        params = {"patient": patient_id, "_sort": "-date", "_count": "50"}
        if observation_type:
            params["category"] = observation_type
        fhir_url = _resolve_fhir_base_url(ctx)
        bundle = await search_fhir_resources_with_url("Observation", params, fhir_url, fhir_token)
        observations = []
        for entry in bundle.get("entry", []):
            obs = entry.get("resource", {})
            observations.append(
                {
                    "id": obs.get("id"),
                    "code": obs.get("code", {}),
                    "value": obs.get("valueQuantity") or obs.get("valueString") or obs.get("valueCodeableConcept"),
                    "effectiveDateTime": obs.get("effectiveDateTime"),
                    "category": obs.get("category", []),
                }
            )
        return {"patient_id": patient_id, "observations": observations, "count": len(observations)}
    except Exception as exc:
        return _error(exc)


@mcp.tool()
async def search_patients(
    family_name: str | None = None,
    given_name: str | None = None,
    identifier: str | None = None,
    fhir_token: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Search for patients by name or identifier."""
    try:
        params = {}
        if family_name:
            params["family"] = family_name
        if given_name:
            params["given"] = given_name
        if identifier:
            params["identifier"] = identifier
        _, fhir_token = _resolve_patient_and_token(None, fhir_token, ctx)
        fhir_url = _resolve_fhir_base_url(ctx)
        bundle = await search_fhir_resources_with_url("Patient", params, fhir_url, fhir_token)
        patients = []
        for entry in bundle.get("entry", []):
            patient = entry.get("resource", {})
            patients.append(
                {
                    "id": patient.get("id"),
                    "name": patient.get("name", [{}])[0],
                    "birthDate": patient.get("birthDate"),
                    "gender": patient.get("gender"),
                }
            )
        return {"patients": patients, "count": len(patients)}
    except Exception as exc:
        return _error(exc)


@mcp.tool()
async def get_prior_auth_summary(
    patient_id: str | None = None,
    fhir_token: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get comprehensive patient summary for prior authorization."""
    try:
        patient_id, fhir_token = _resolve_patient_and_token(patient_id, fhir_token, ctx)
        if not patient_id:
            return {"error": "Missing patient_id (or X-Patient-ID context header)", "type": "ValidationError"}
        fhir_url = _resolve_fhir_base_url(ctx)
        patient_task = fetch_fhir_resource_with_url("Patient", patient_id, fhir_url, fhir_token)
        conditions_task = search_fhir_resources_with_url("Condition", {"patient": patient_id}, fhir_url, fhir_token)
        meds_task = search_fhir_resources_with_url("MedicationRequest", {"patient": patient_id}, fhir_url, fhir_token)
        procedures_task = search_fhir_resources_with_url("Procedure", {"patient": patient_id}, fhir_url, fhir_token)
        obs_task = search_fhir_resources_with_url("Observation", {"patient": patient_id, "_count": "20"}, fhir_url, fhir_token)

        patient, conditions_bundle, meds_bundle, procedures_bundle, obs_bundle = await asyncio.gather(
            patient_task, conditions_task, meds_task, procedures_task, obs_task, return_exceptions=True
        )

        summary = {
            "patient": {
                "id": patient.get("id") if not isinstance(patient, Exception) else None,
                "name": patient.get("name", [{}])[0] if not isinstance(patient, Exception) else {},
                "birthDate": patient.get("birthDate") if not isinstance(patient, Exception) else None,
                "gender": patient.get("gender") if not isinstance(patient, Exception) else None,
            },
            "active_conditions": [],
            "current_medications": [],
            "recent_procedures": [],
            "recent_labs": [],
        }

        if not isinstance(conditions_bundle, Exception):
            for entry in conditions_bundle.get("entry", [])[:10]:
                condition = entry.get("resource", {})
                if condition.get("clinicalStatus", {}).get("coding", [{}])[0].get("code") == "active":
                    summary["active_conditions"].append(
                        {
                            "display": condition.get("code", {}).get("text"),
                            "codes": condition.get("code", {}).get("coding", []),
                        }
                    )

        if not isinstance(meds_bundle, Exception):
            for entry in meds_bundle.get("entry", [])[:10]:
                med = entry.get("resource", {})
                if med.get("status") in ["active", "completed"]:
                    summary["current_medications"].append(
                        {"display": med.get("medicationCodeableConcept", {}).get("text"), "status": med.get("status")}
                    )

        if not isinstance(procedures_bundle, Exception):
            for entry in procedures_bundle.get("entry", [])[:5]:
                procedure = entry.get("resource", {})
                summary["recent_procedures"].append(
                    {"display": procedure.get("code", {}).get("text"), "date": procedure.get("performedDateTime")}
                )

        if not isinstance(obs_bundle, Exception):
            for entry in obs_bundle.get("entry", [])[:10]:
                obs = entry.get("resource", {})
                summary["recent_labs"].append(
                    {
                        "display": obs.get("code", {}).get("text"),
                        "value": obs.get("valueQuantity") or obs.get("valueString"),
                        "date": obs.get("effectiveDateTime"),
                    }
                )

        return summary
    except Exception as exc:
        return _error(exc)


async def call_tool(name: str, arguments: Any) -> list[Any]:
    class _Text:
        def __init__(self, text: str):
            self.text = text

    handlers = {
        "get_patient_demographics": lambda: get_patient_demographics(**arguments),
        "get_patient_conditions": lambda: get_patient_conditions(**arguments),
        "get_patient_medications": lambda: get_patient_medications(**arguments),
        "get_patient_procedures": lambda: get_patient_procedures(**arguments),
        "get_patient_observations": lambda: get_patient_observations(**arguments),
        "search_patients": lambda: search_patients(**arguments),
        "get_prior_auth_summary": lambda: get_prior_auth_summary(**arguments),
    }
    if name not in handlers:
        return [_Text(json.dumps({"error": f"Unknown tool: {name}"}))]
    result = await handlers[name]()
    return [_Text(json.dumps(result, indent=2))]


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)
