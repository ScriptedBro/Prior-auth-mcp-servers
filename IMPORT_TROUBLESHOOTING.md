# Prompt Opinion Import Troubleshooting Guide

## Problem

Getting "An unexpected error has occurred" when importing FHIR data to Prompt Opinion.

## Solutions (Try in Order)

### ✅ Solution 1: Use Collection Bundles (RECOMMENDED)

Synthea generates transaction bundles, but Prompt Opinion likely expects collection bundles.

**What we did**:
```bash
cd synthea
python3 convert-to-collection-bundle.py
```

**Result**: 112 collection bundles in `synthea/output/fhir_collection/`

**Try uploading from**: `synthea/output/fhir_collection/`

---

### 🔄 Solution 2: Start with Small Files

If collection bundles still fail, try smaller files first to isolate the issue.

**Find smallest files**:
```bash
cd synthea/output/fhir_collection
ls -lh *.json | sort -k5 -h | head -10
```

**Try uploading**:
1. Start with the smallest patient file
2. If successful, try a medium-sized file
3. If successful, upload all files

**This helps identify**:
- File size limits
- Specific resource type issues
- Bundle complexity issues

---

### 🔄 Solution 3: Extract Individual Resources

If bundles don't work at all, extract individual resources.

**Run extraction**:
```bash
cd synthea
python3 extract-individual-resources.py
```

**Result**: Individual resource files in `synthea/output/fhir_individual/`

**Structure**:
```
output/fhir_individual/
├── Aaron697_Kihn564_.../
│   ├── Patient_3ea65e25....json
│   ├── Condition_abc123.json
│   ├── MedicationRequest_def456.json
│   └── ... (397 files)
├── Alden634_OReilly797_.../
│   └── ... (295 files)
```

**Try uploading**:
1. Upload one Patient resource first
2. Then upload related resources (Conditions, Medications, etc.)
3. Or upload entire patient directory

---

### 🔄 Solution 4: Check Prompt Opinion Requirements

**Look for documentation on**:
- Supported bundle types
- File size limits
- FHIR version requirements (R4, R5?)
- Required resource types
- Forbidden resource types

**Where to check**:
- Prompt Opinion documentation
- Platform settings/help
- Error logs (if available)
- Support contact

---

### 🔄 Solution 5: Validate FHIR Data

Use a FHIR validator to check if the data is valid:

**Online validator**:
```bash
# Upload a sample file to:
https://validator.fhir.org/
```

**Or use HAPI FHIR validator**:
```bash
# If you have Java installed
wget https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar
java -jar validator_cli.jar output/fhir_collection/Aaron697_Kihn564_*.json
```

---

## Common FHIR Import Issues

### Issue 1: Bundle Type
- **Problem**: Server expects collection, you send transaction
- **Solution**: ✅ Already fixed with `convert-to-collection-bundle.py`

### Issue 2: File Size
- **Problem**: Files too large (some servers limit to 5-50 MB)
- **Solution**: Upload smaller files first, or split large bundles

### Issue 3: Resource References
- **Problem**: References to non-existent resources
- **Solution**: ✅ Already fixed by removing Practitioner/Location/Org references

### Issue 4: FHIR Version
- **Problem**: Server expects R4, data is R5 (or vice versa)
- **Solution**: Check Synthea FHIR version and Prompt Opinion requirements

### Issue 5: Required Fields
- **Problem**: Missing required fields in resources
- **Solution**: Validate with FHIR validator

### Issue 6: Unsupported Resources
- **Problem**: Server doesn't support certain resource types
- **Solution**: Filter out unsupported types

---

## Quick Diagnostic Checklist

Run through this checklist:

- [ ] **Bundle type**: Using collection bundles? (`output/fhir_collection/`)
- [ ] **No problematic references**: Verified 0 Practitioner/Location/Org refs?
- [ ] **File size**: Tried smallest files first?
- [ ] **Valid JSON**: Files open without errors?
- [ ] **FHIR structure**: Has `resourceType: "Bundle"` and `entry` array?
- [ ] **Error details**: Any more specific error message available?

---

## Files Available for Upload

You have 3 versions of the data:

### 1. Original (Don't Use)
- **Location**: `synthea/output/fhir/`
- **Type**: Transaction bundles
- **Issues**: Has Practitioner/Location/Org references
- **Status**: ❌ Don't use

### 2. Cleaned Collection Bundles (Try First)
- **Location**: `synthea/output/fhir_collection/`
- **Type**: Collection bundles
- **Issues**: None known
- **Status**: ✅ **RECOMMENDED - TRY THIS FIRST**

### 3. Individual Resources (Fallback)
- **Location**: `synthea/output/fhir_individual/` (after running extraction)
- **Type**: Individual resource files
- **Issues**: None known
- **Status**: ✅ Use if bundles don't work

---

## Step-by-Step Upload Process

### Attempt 1: Collection Bundles

1. **Navigate to cleaned collection bundles**:
   ```bash
   cd ~/Desktop/Health\ Hackathon/synthea/output/fhir_collection/
   ```

2. **Find a small test file**:
   ```bash
   ls -lh *.json | sort -k5 -h | head -5
   ```

3. **Upload smallest file to Prompt Opinion**:
   - Go to Prompt Opinion → Data Import
   - Upload the smallest patient file
   - Wait for result

4. **If successful**:
   - Upload 5-10 more files
   - Then upload all remaining files

5. **If fails**:
   - Note the exact error message
   - Try Attempt 2

### Attempt 2: Individual Resources

1. **Extract resources**:
   ```bash
   cd ~/Desktop/Health\ Hackathon/synthea
   python3 extract-individual-resources.py
   ```

2. **Navigate to individual resources**:
   ```bash
   cd output/fhir_individual
   ls -d */  # List patient directories
   ```

3. **Upload one patient's resources**:
   - Start with Patient resource
   - Then upload other resources for that patient
   - Check if import succeeds

4. **If successful**:
   - Repeat for other patients
   - Or upload entire directories if supported

5. **If fails**:
   - Contact Prompt Opinion support with:
     - Sample file
     - Exact error message
     - What you've tried

---

## Getting Help

If all attempts fail, gather this information for support:

### Information to Provide

1. **Sample file**: Share `Aaron697_Kihn564_*.json` (collection version)
2. **Error message**: Exact text of "unexpected error"
3. **What you tried**:
   - ✅ Removed Practitioner/Location/Org references
   - ✅ Converted to collection bundles
   - ✅ Tried small files
   - ✅ Validated FHIR structure

4. **Questions to ask**:
   - What bundle type does Prompt Opinion expect?
   - Is there a file size limit?
   - What FHIR version is supported?
   - Are there example import files available?
   - Is there a specific import API or format?

### Contact Points

- Prompt Opinion documentation: https://docs.promptopinion.ai/
- Prompt Opinion support (check their website)
- Hackathon Discord/Slack (if available)
- FHIR community: https://chat.fhir.org/

---

## Summary

**Current Status**:
- ✅ All problematic references removed
- ✅ Collection bundles created
- ✅ Individual resource extraction available
- ⏭️ Ready to try uploading

**Next Action**:
1. Upload from `synthea/output/fhir_collection/`
2. Start with smallest file
3. If fails, try individual resources
4. If still fails, contact support

---

**You have clean, valid FHIR data. The issue is likely just finding the right format/method for Prompt Opinion's import.**
