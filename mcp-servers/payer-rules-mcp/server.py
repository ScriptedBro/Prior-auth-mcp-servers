#!/usr/bin/env python3
"""
Payer Rules MCP Server
Provides prior authorization rules and criteria for different payers and procedures.
Supports both stdio and streamable HTTP transports.
"""

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Payer Rules Database
# Covers all 3 PA demo scenarios exactly:
#   Scenario 1 — Aetna PPO          : MRI Lumbar Spine (CPT 72148)
#   Scenario 2 — UnitedHealthcare   : Humira / adalimumab (J0135)
#   Scenario 3 — Humana Medicare Adv: Nuclear Stress Test (CPT 78452)
# ---------------------------------------------------------------------------
PAYER_RULES: dict[str, dict[str, Any]] = {
    "Aetna PPO": {
        "MRI Lumbar Spine": {
            "requires_auth": True,
            "cpt_code": "72148",
            "description": "MRI Lumbar Spine without contrast",
            "icd10_codes": ["M54.5", "M51.16", "M51.17", "M54.4"],
            "criteria": [
                {
                    "id": "conservative_treatment",
                    "description": "Conservative treatment >= 6 weeks (PT, chiropractic, or NSAID therapy)",
                    "required": True,
                    "evidence_fields": ["procedures", "medications"],
                },
                {
                    "id": "pain_duration",
                    "description": "Pain duration >= 3 months",
                    "required": True,
                    "evidence_fields": ["conditions"],
                },
                {
                    "id": "physician_visit",
                    "description": "Minimum 1 physician office visit documented",
                    "required": True,
                    "evidence_fields": ["encounters"],
                },
                {
                    "id": "functional_impairment",
                    "description": "Neurological symptoms OR functional impairment documented",
                    "required": True,
                    "evidence_fields": ["observations", "conditions"],
                },
            ],
            "turnaround_time_hours": 48,
            "appeal_deadline_days": 30,
            "notes": "Urgent requests (red flag symptoms) processed within 24 hours.",
        },
        "CT Scan Abdomen": {
            "requires_auth": True,
            "cpt_code": "74178",
            "description": "CT scan abdomen and pelvis with contrast",
            "icd10_codes": ["R10.9", "K92.1", "C18.9"],
            "criteria": [
                {
                    "id": "clinical_indication",
                    "description": "Clinical indication documented by ordering physician",
                    "required": True,
                    "evidence_fields": ["conditions"],
                },
                {
                    "id": "prior_imaging",
                    "description": "Prior basic imaging (X-ray or ultrasound) completed if applicable",
                    "required": False,
                    "evidence_fields": ["procedures"],
                },
            ],
            "turnaround_time_hours": 24,
            "appeal_deadline_days": 30,
        },
        "Specialist Referral - Cardiology": {
            "requires_auth": False,
            "description": "Cardiology specialist referral",
            "criteria": [
                {
                    "id": "pcp_referral",
                    "description": "PCP referral documentation required",
                    "required": True,
                    "evidence_fields": ["encounters"],
                }
            ],
            "turnaround_time_hours": 0,
            "appeal_deadline_days": 0,
            "notes": "No prior auth needed but PCP referral must be on file.",
        },
    },

    "UnitedHealthcare Choice Plus": {
        "Humira (adalimumab)": {
            "requires_auth": True,
            "drug_code": "J0135",
            "description": "Adalimumab (Humira) 40mg subcutaneous injection",
            "icd10_codes": ["M05.79", "M05.9", "M06.9", "K50.90", "L40.50"],
            "criteria": [
                {
                    "id": "ra_diagnosis",
                    "description": "Confirmed RA diagnosis (ICD-10: M05.x or M06.x)",
                    "required": True,
                    "evidence_fields": ["conditions"],
                },
                {
                    "id": "methotrexate_trial",
                    "description": "Methotrexate trial >= 3 months with documented inadequate response",
                    "required": True,
                    "evidence_fields": ["medications", "observations"],
                },
                {
                    "id": "second_dmard_trial",
                    "description": "Second DMARD trial required (Leflunomide or Sulfasalazine)",
                    "required": True,
                    "evidence_fields": ["medications"],
                },
                {
                    "id": "tb_screening",
                    "description": "TB screening (QuantiFERON or TST) completed within 12 months",
                    "required": True,
                    "evidence_fields": ["observations", "procedures"],
                },
            ],
            "step_therapy": ["Methotrexate", "Leflunomide", "Sulfasalazine"],
            "turnaround_time_hours": 72,
            "appeal_deadline_days": 60,
            "notes": (
                "Step therapy exceptions may apply if second DMARD is contraindicated. "
                "Physician must document clinical rationale for exception."
            ),
        },
        "MRI": {
            "requires_auth": True,
            "cpt_code": "72148",
            "description": "MRI Lumbar Spine without contrast",
            "icd10_codes": ["M54.5", "M51.16", "S13.4"],
            "criteria": [
                {
                    "id": "conservative_treatment",
                    "description": "Conservative treatment attempted for >= 4 weeks",
                    "required": True,
                    "evidence_fields": ["procedures", "medications"],
                },
                {
                    "id": "clinical_necessity",
                    "description": "Clinical necessity documented by ordering physician",
                    "required": True,
                    "evidence_fields": ["conditions", "observations"],
                },
            ],
            "turnaround_time_hours": 24,
            "appeal_deadline_days": 30,
        },
        "Specialist Referral - Orthopedics": {
            "requires_auth": True,
            "description": "Orthopedic specialist referral",
            "criteria": [
                {
                    "id": "pcp_evaluation",
                    "description": "PCP evaluation completed and documented",
                    "required": True,
                    "evidence_fields": ["encounters"],
                },
                {
                    "id": "basic_imaging",
                    "description": "X-ray or basic imaging completed",
                    "required": True,
                    "evidence_fields": ["procedures"],
                },
            ],
            "turnaround_time_hours": 48,
            "appeal_deadline_days": 30,
        },
    },

    "Humana Medicare Advantage": {
        "Nuclear Stress Test": {
            "requires_auth": True,
            "cpt_code": "78452",
            "description": "Myocardial Perfusion Imaging (Nuclear Stress Test)",
            "icd10_codes": ["I25.10", "I25.110", "R07.9", "I20.9", "Z87.39"],
            "criteria": [
                {
                    "id": "cad_diagnosis",
                    "description": "CAD or chest pain diagnosis documented (ICD-10: I25.x or R07.x)",
                    "required": True,
                    "evidence_fields": ["conditions"],
                },
                {
                    "id": "symptom_documentation",
                    "description": "Symptomatic chest pain onset date and frequency documented",
                    "required": True,
                    "evidence_fields": ["observations", "conditions"],
                },
                {
                    "id": "prior_stress_test",
                    "description": "Prior stress test results provided if this is repeat imaging",
                    "required": False,
                    "evidence_fields": ["procedures"],
                },
                {
                    "id": "antianginal_medications",
                    "description": "Current antianginal medications listed (if applicable)",
                    "required": False,
                    "evidence_fields": ["medications"],
                },
            ],
            "turnaround_time_hours": 48,
            "appeal_deadline_days": 30,
            "notes": (
                "Medicare Advantage plans follow CMS coverage guidelines. "
                "Expedited review (72hr) available for symptomatic unstable patients."
            ),
        },
        "Echocardiogram": {
            "requires_auth": True,
            "cpt_code": "93306",
            "description": "Transthoracic echocardiogram with Doppler",
            "icd10_codes": ["I50.9", "I25.10", "I34.0"],
            "criteria": [
                {
                    "id": "cardiac_diagnosis",
                    "description": "Documented cardiac diagnosis requiring structural evaluation",
                    "required": True,
                    "evidence_fields": ["conditions"],
                },
                {
                    "id": "clinical_indication",
                    "description": "Clinical indication: new murmur, CHF evaluation, or post-MI",
                    "required": True,
                    "evidence_fields": ["conditions", "observations"],
                },
            ],
            "turnaround_time_hours": 48,
            "appeal_deadline_days": 30,
        },
    },

    "Blue Cross Blue Shield": {
        "MRI Lumbar Spine": {
            "requires_auth": True,
            "cpt_code": "72148",
            "description": "MRI Lumbar Spine without contrast",
            "icd10_codes": ["M54.5", "M51.16", "G89.29"],
            "criteria": [
                {
                    "id": "conservative_treatment",
                    "description": "Failed conservative treatment for >= 6 weeks",
                    "required": True,
                    "evidence_fields": ["procedures", "medications"],
                },
                {
                    "id": "clinical_indication",
                    "description": "Documented clinical indication (suspected herniated disc, tumor, or stenosis)",
                    "required": True,
                    "evidence_fields": ["conditions"],
                },
            ],
            "turnaround_time_hours": 48,
            "appeal_deadline_days": 30,
        },
        "Humira (adalimumab)": {
            "requires_auth": True,
            "drug_code": "J0135",
            "description": "Adalimumab (Humira) 40mg subcutaneous injection",
            "icd10_codes": ["M05.79", "K50.90", "L40.50"],
            "criteria": [
                {
                    "id": "diagnosis_confirmed",
                    "description": "Diagnosis of RA, Crohn's disease, or psoriasis confirmed",
                    "required": True,
                    "evidence_fields": ["conditions"],
                },
                {
                    "id": "dmard_failure",
                    "description": "Failed at least 2 conventional DMARDs",
                    "required": True,
                    "evidence_fields": ["medications"],
                },
                {
                    "id": "tb_screening",
                    "description": "TB screening completed",
                    "required": True,
                    "evidence_fields": ["observations", "procedures"],
                },
            ],
            "step_therapy": ["Methotrexate", "Sulfasalazine"],
            "turnaround_time_hours": 72,
            "appeal_deadline_days": 60,
        },
    },
}


# ---------------------------------------------------------------------------
# Server bootstrap (mirrors patient-records-mcp pattern exactly)
# ---------------------------------------------------------------------------

def _server() -> FastMCP:
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "9001")))
    path = os.getenv("MCP_PATH", "/mcp")

    server = FastMCP("payer-rules-mcp", host=host, port=port, streamable_http_path=path)

    fhir_extension: dict[str, Any] = {"ai.promptopinion/fhir-context": {"scopes": []}}
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error(message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": message}
    payload.update(extra)
    return payload


def _fuzzy_match(query: str, options: list[str]) -> str | None:
    """Case-insensitive partial match — lets agents call tools without exact casing."""
    q = query.lower()
    for option in options:
        if q in option.lower() or option.lower() in q:
            return option
    return None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_payers() -> dict[str, Any]:
    """List all insurance payers available in the rules database."""
    payers = list(PAYER_RULES.keys())
    return {"payers": payers, "count": len(payers)}


@mcp.tool()
async def list_procedures(payer: str) -> dict[str, Any]:
    """List all procedures and medications covered under a specific payer."""
    matched_payer = _fuzzy_match(payer, list(PAYER_RULES.keys()))
    if not matched_payer:
        return _error(f"Payer '{payer}' not found", available_payers=list(PAYER_RULES.keys()))

    procedures = list(PAYER_RULES[matched_payer].keys())
    return {"payer": matched_payer, "procedures": procedures, "count": len(procedures)}


@mcp.tool()
async def check_auth_requirements(payer: str, procedure_or_medication: str) -> dict[str, Any]:
    """Check whether a procedure or medication requires prior authorization for a given payer."""
    matched_payer = _fuzzy_match(payer, list(PAYER_RULES.keys()))
    if not matched_payer:
        return _error(f"Payer '{payer}' not found", available_payers=list(PAYER_RULES.keys()))

    matched_proc = _fuzzy_match(procedure_or_medication, list(PAYER_RULES[matched_payer].keys()))
    if not matched_proc:
        return _error(
            f"Procedure '{procedure_or_medication}' not found for payer '{matched_payer}'",
            available_procedures=list(PAYER_RULES[matched_payer].keys()),
        )

    rule = PAYER_RULES[matched_payer][matched_proc]
    return {
        "payer": matched_payer,
        "procedure_or_medication": matched_proc,
        "requires_prior_authorization": rule["requires_auth"],
        "turnaround_time_hours": rule.get("turnaround_time_hours", 0),
        "appeal_deadline_days": rule.get("appeal_deadline_days", 30),
        "cpt_or_drug_code": rule.get("cpt_code") or rule.get("drug_code"),
    }


@mcp.tool()
async def get_auth_criteria(payer: str, procedure_or_medication: str) -> dict[str, Any]:
    """Get the full prior authorization criteria for a payer and procedure or medication."""
    matched_payer = _fuzzy_match(payer, list(PAYER_RULES.keys()))
    if not matched_payer:
        return _error(f"Payer '{payer}' not found")

    matched_proc = _fuzzy_match(procedure_or_medication, list(PAYER_RULES[matched_payer].keys()))
    if not matched_proc:
        return _error(f"Procedure '{procedure_or_medication}' not found for payer '{matched_payer}'")

    rule = PAYER_RULES[matched_payer][matched_proc]
    return {
        "payer": matched_payer,
        "procedure_or_medication": matched_proc,
        "requires_auth": rule["requires_auth"],
        "cpt_or_drug_code": rule.get("cpt_code") or rule.get("drug_code"),
        "icd10_codes": rule.get("icd10_codes", []),
        "criteria": rule.get("criteria", []),
        "step_therapy": rule.get("step_therapy", []),
        "turnaround_time_hours": rule.get("turnaround_time_hours", 0),
        "appeal_deadline_days": rule.get("appeal_deadline_days", 30),
        "notes": rule.get("notes", ""),
    }


@mcp.tool()
async def evaluate_criteria(
    payer: str,
    procedure_or_medication: str,
    patient_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate whether a patient's clinical data meets payer prior authorization criteria.

    patient_data should be the output from the Patient Records MCP get_prior_auth_summary tool:
    {
        "active_conditions": [...],
        "current_medications": [...],
        "recent_procedures": [...],
        "recent_labs": [...],
    }

    Returns a breakdown of met/unmet criteria and a recommendation.
    """
    matched_payer = _fuzzy_match(payer, list(PAYER_RULES.keys()))
    if not matched_payer:
        return _error(f"Payer '{payer}' not found")

    matched_proc = _fuzzy_match(procedure_or_medication, list(PAYER_RULES[matched_payer].keys()))
    if not matched_proc:
        return _error(f"Procedure '{procedure_or_medication}' not found for payer '{matched_payer}'")

    rule = PAYER_RULES[matched_payer][matched_proc]
    criteria = rule.get("criteria", [])

    # Flatten patient data into searchable text for each evidence type
    evidence: dict[str, str] = {
        "conditions": " ".join(
            (c.get("display") or c.get("code", {}).get("text") or "")
            for c in patient_data.get("active_conditions", [])
        ).lower(),
        "medications": " ".join(
            (m.get("display") or m.get("medication", {}).get("text") or "")
            for m in patient_data.get("current_medications", [])
        ).lower(),
        "procedures": " ".join(
            (p.get("display") or p.get("code", {}).get("text") or "")
            for p in patient_data.get("recent_procedures", [])
        ).lower(),
        "observations": " ".join(
            (o.get("display") or o.get("code", {}).get("text") or "")
            for o in patient_data.get("recent_labs", [])
        ).lower(),
        "encounters": str(len(patient_data.get("recent_procedures", []))),
    }

    # Keyword map for each criterion — used for automated evidence matching
    CRITERION_KEYWORDS: dict[str, list[str]] = {
        "conservative_treatment": ["physical therapy", "pt ", "chiropractic", "ibuprofen", "nsaid", "naproxen", "therapy"],
        "pain_duration": ["back pain", "chronic", "low back", "lumbago", "pain"],
        "physician_visit": ["visit", "encounter", "office", "consultation"],
        "functional_impairment": ["impairment", "radiculopathy", "weakness", "numbness", "stenosis", "herniat"],
        "ra_diagnosis": ["rheumatoid", "arthritis", "m05", "m06"],
        "methotrexate_trial": ["methotrexate"],
        "second_dmard_trial": ["leflunomide", "sulfasalazine", "hydroxychloroquine"],
        "tb_screening": ["tb", "tuberculosis", "quantiferon", "tst", "ppd"],
        "diagnosis_confirmed": ["rheumatoid", "crohn", "psoriasis", "arthritis"],
        "dmard_failure": ["methotrexate", "sulfasalazine", "leflunomide", "hydroxychloroquine"],
        "cad_diagnosis": ["coronary", "ischemic", "chest pain", "angina", "i25", "r07", "cad"],
        "symptom_documentation": ["chest pain", "angina", "dyspnea", "shortness of breath", "palpitation"],
        "prior_stress_test": ["stress test", "nuclear", "perfusion", "exercise test"],
        "antianginal_medications": ["nitrate", "beta blocker", "metoprolol", "atenolol", "amlodipine", "isosorbide"],
        "pcp_referral": ["referral", "pcp", "primary care"],
        "pcp_evaluation": ["evaluation", "office visit", "primary care"],
        "basic_imaging": ["x-ray", "xray", "radiograph", "plain film"],
        "clinical_indication": ["diagnosis", "condition", "clinical"],
        "cardiac_diagnosis": ["heart failure", "chf", "murmur", "cardiomyopathy", "valve"],
        "prior_imaging": ["x-ray", "ultrasound", "imaging", "radiograph"],
        "clinical_necessity": ["clinical", "necessity", "indication"],
    }

    met: list[dict[str, Any]] = []
    unmet: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []

    for criterion in criteria:
        cid = criterion["id"]
        keywords = CRITERION_KEYWORDS.get(cid, [])
        evidence_fields = criterion.get("evidence_fields", list(evidence.keys()))

        # Search relevant evidence fields for keywords
        found = False
        matched_in = []
        for field in evidence_fields:
            field_text = evidence.get(field, "")
            for kw in keywords:
                if kw in field_text:
                    found = True
                    matched_in.append(field)
                    break

        entry = {
            "criterion_id": cid,
            "description": criterion["description"],
            "required": criterion.get("required", True),
        }

        if found:
            entry["evidence_found_in"] = list(set(matched_in))
            met.append(entry)
        elif not keywords:
            entry["note"] = "No automated check available — manual review required"
            unknown.append(entry)
        else:
            entry["missing_evidence"] = f"No evidence found in: {', '.join(evidence_fields)}"
            unmet.append(entry)

    # Determine recommendation
    required_unmet = [c for c in unmet if c.get("required", True)]
    required_unknown = [c for c in unknown if c.get("required", True)]

    if not required_unmet and not required_unknown:
        recommendation = "approve"
        confidence = round(1.0 - (len(unmet) * 0.05), 2)
        summary = "All required criteria met. PA likely to be approved."
    elif required_unknown:
        recommendation = "incomplete"
        confidence = 0.0
        summary = f"{len(required_unknown)} required criteria could not be automatically verified. Manual review needed."
    else:
        recommendation = "deny"
        confidence = 0.0
        summary = f"{len(required_unmet)} required criteria not met. Consider appeal or step therapy."

    return {
        "payer": matched_payer,
        "procedure_or_medication": matched_proc,
        "recommendation": recommendation,
        "confidence_score": confidence,
        "summary": summary,
        "criteria_met": met,
        "criteria_unmet": unmet,
        "criteria_unknown": unknown,
        "total_criteria": len(criteria),
        "met_count": len(met),
        "unmet_count": len(unmet),
        "step_therapy": rule.get("step_therapy", []),
        "appeal_deadline_days": rule.get("appeal_deadline_days", 30),
    }


# ---------------------------------------------------------------------------
# Backwards-compatible call_tool helper for local tests
# ---------------------------------------------------------------------------

async def call_tool(name: str, arguments: Any) -> list[Any]:
    class _Text:
        def __init__(self, text: str):
            self.text = text

    handlers = {
        "list_payers": lambda: list_payers(),
        "list_procedures": lambda: list_procedures(**arguments),
        "check_auth_requirements": lambda: check_auth_requirements(**arguments),
        "get_auth_criteria": lambda: get_auth_criteria(**arguments),
        "evaluate_criteria": lambda: evaluate_criteria(**arguments),
    }

    if name not in handlers:
        return [_Text(json.dumps(_error(f"Unknown tool: {name}")))]

    result = await handlers[name]()
    if isinstance(result, str):
        return [_Text(result)]
    return [_Text(json.dumps(result, indent=2))]


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)
