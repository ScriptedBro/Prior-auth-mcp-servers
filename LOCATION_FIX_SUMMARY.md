# Location Reference Fix - Summary

## Problem Encountered

After fixing the Practitioner reference errors, uploading Synthea FHIR data to Prompt Opinion resulted in a new error:

```
No resources found that match conditional reference: 
Location?identifier=https://github.com/synthetichealth/synthea|1c76c5e9-c508-37a9-9c26-074024a1140c
```

## Root Cause

The cleaning script was removing Location resources but **not** removing references to those locations in other resources. Specifically:

- **Claim** resources have a `facility` field that references Location
- **ExplanationOfBenefit** resources have a `facility` field that references Location

## Solution Implemented

Updated `synthea/clean-fhir-for-prompt-opinion.py` to remove the `facility` field from all resources:

```python
# Remove facility field (location reference in Claim/ExplanationOfBenefit)
if "facility" in resource:
    del resource["facility"]
```

## Verification

After re-running the cleaning script:

```bash
cd synthea
python3 clean-fhir-for-prompt-opinion.py
```

Results:
- ✅ 112 files successfully cleaned
- ✅ 0 Location references remaining (verified with grep)
- ✅ All patient clinical data preserved

```bash
# Verification command
grep -r "Location?identifier" synthea/output/fhir_clean/
# Returns: 0 matches
```

## What's Now Removed

### Resources:
- ❌ Practitioner
- ❌ PractitionerRole
- ❌ Location
- ❌ Organization

### Reference Fields:
- ❌ participant
- ❌ performer
- ❌ generalPractitioner
- ❌ requester
- ❌ recorder
- ❌ asserter
- ❌ location (in Encounter)
- ❌ **facility** (in Claim/ExplanationOfBenefit) ← **NEW FIX**
- ❌ serviceProvider
- ❌ managingOrganization
- ❌ basedOn

## What's Preserved

All clinically relevant data for prior authorization:

| Resource Type | Count (sample) | Purpose |
|--------------|----------------|---------|
| Patient | 1 | Demographics |
| Condition | 16 | Diagnoses (ICD-10) |
| MedicationRequest | 3 | Prescriptions |
| Procedure | 71 | Treatment history |
| Observation | 111 | Labs, vitals |
| Encounter | 27 | Visit history |
| Claim | 30 | Billing info |
| ExplanationOfBenefit | 30 | Insurance claims |
| Immunization | 20 | Vaccinations |
| DiagnosticReport | 33 | Test results |
| CarePlan | 1 | Treatment plans |

**Total entries per patient**: ~397 resources

## Next Steps

1. ✅ **DONE**: Location references removed
2. ⏭️ **TODO**: Upload cleaned files to Prompt Opinion
3. ⏭️ **TODO**: Verify import succeeds without errors
4. ⏭️ **TODO**: Test patient data access via MCP servers
5. ⏭️ **TODO**: Test complete prior auth workflow

## Files Modified

- `synthea/clean-fhir-for-prompt-opinion.py` - Added facility field removal
- `synthea/CLEANED_DATA_GUIDE.md` - Updated documentation
- `synthea/output/fhir_clean/*.json` - All 112 files re-cleaned

## Upload Instructions

The cleaned data is ready to upload to Prompt Opinion:

1. Go to Prompt Opinion → Patient Data → Import
2. Click "Upload a FHIR Bundle"
3. Select files from `synthea/output/fhir_clean/`
4. Click "Import"
5. ✅ Should succeed without conditional reference errors

## Technical Details

### Discovery Process

1. Ran cleaning script (removed Practitioner/PractitionerRole)
2. Attempted upload → Got Location reference error
3. Searched for Location references in cleaned files:
   ```bash
   grep -i "Location?identifier" output/fhir_clean/*.json
   ```
4. Found references still present
5. Analyzed structure to find exact field:
   ```python
   # Found: Claim.facility and ExplanationOfBenefit.facility
   ```
6. Updated script to remove `facility` field
7. Re-ran cleaning script
8. Verified 0 Location references remain

### Why This Matters

Prompt Opinion validates all FHIR references during import. Conditional references like:

```json
{
  "facility": {
    "reference": "Location?identifier=https://github.com/synthetichealth/synthea|abc123"
  }
}
```

...are not supported because:
- The Location resource doesn't exist in Prompt Opinion
- Conditional references require special resolution logic
- Synthea uses GitHub URLs as identifiers (non-standard)

By removing these references, we ensure clean imports while preserving all clinical data needed for prior authorization.

---

**Status**: ✅ Ready for Prompt Opinion upload
**Last Updated**: 2026-05-07
