# Bundle Type Fix - Transaction to Collection

## Problem

When uploading cleaned FHIR data to Prompt Opinion, you got:
```
An unexpected error has occurred.
```

## Root Cause

Synthea generates **transaction bundles** which include:
- `type: "transaction"` in the bundle
- `request` fields in each entry (with HTTP methods like POST, PUT)
- Designed for batch operations on FHIR servers

Many FHIR import tools expect **collection bundles** which are simpler:
- `type: "collection"` in the bundle
- No `request` fields
- Just a collection of resources for import

## Solution

Created `convert-to-collection-bundle.py` to convert transaction bundles to collection bundles.

### What It Does

1. Changes `bundle.type` from `"transaction"` to `"collection"`
2. Removes all `request` fields from entries
3. Keeps all resources and their data intact

### Before (Transaction Bundle)
```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "fullUrl": "urn:uuid:...",
      "resource": { ... },
      "request": {
        "method": "POST",
        "url": "Patient"
      }
    }
  ]
}
```

### After (Collection Bundle)
```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "fullUrl": "urn:uuid:...",
      "resource": { ... }
    }
  ]
}
```

## How to Use

### Step 1: Convert Bundles

```bash
cd synthea
python3 convert-to-collection-bundle.py
```

**Output**:
- ✅ 112 files converted
- 📂 Saved to `output/fhir_collection/`

### Step 2: Upload Collection Bundles

Upload files from `synthea/output/fhir_collection/` instead of `output/fhir_clean/`

## Verification

Check that conversion worked:

```bash
cd synthea

# Check bundle type
python3 -c "
import json
with open('output/fhir_collection/Aaron697_Kihn564_3ea65e25-138a-274e-6448-a79905083f22.json') as f:
    bundle = json.load(f)
    print('Type:', bundle.get('type'))
    print('Has request fields:', any('request' in e for e in bundle.get('entry', [])))
"
```

**Expected output**:
```
Type: collection
Has request fields: False
```

## Files Created

1. **`synthea/convert-to-collection-bundle.py`** - Conversion script
2. **`synthea/output/fhir_collection/*.json`** - 112 collection bundles

## What's Preserved

All data is preserved:
- ✅ All resources (Patient, Condition, Medication, etc.)
- ✅ All clinical data
- ✅ All resource IDs and references
- ✅ All metadata

Only removed:
- ❌ `request` fields (HTTP operation metadata)
- ❌ `type: "transaction"` (changed to `"collection"`)

## Upload Instructions

### Try with One File First

1. Go to Prompt Opinion → Data Import
2. Upload `synthea/output/fhir_collection/Aaron697_Kihn564_3ea65e25-138a-274e-6448-a79905083f22.json`
3. Check for errors

### If Successful, Upload All

1. Select all files from `synthea/output/fhir_collection/`
2. Upload to Prompt Opinion
3. Verify patients appear in the system

## Alternative: Individual Resources

If collection bundles still don't work, Prompt Opinion might want individual resources. Let me know and I can create a script to:
1. Extract each resource from the bundle
2. Save as individual JSON files
3. Upload one resource at a time

## Troubleshooting

### Still Getting "Unexpected Error"

Try these approaches in order:

#### Option 1: Smaller Bundles
Some systems have size limits. Try uploading smaller patient files first:
```bash
ls -lh output/fhir_collection/*.json | sort -k5 -h | head -10
```

#### Option 2: Individual Resources
Extract resources from bundles and upload individually:
```python
# I can create this script if needed
python3 extract-individual-resources.py
```

#### Option 3: Check Prompt Opinion Docs
- Look for FHIR import documentation
- Check if there's a specific format required
- See if there's a file size limit
- Check if there's a specific FHIR version required

#### Option 4: Contact Prompt Opinion Support
Provide them with:
- Sample file (Aaron697 patient)
- Error message
- Ask about expected bundle format

## Bundle Types Explained

| Type | Purpose | Has Requests | Use Case |
|------|---------|--------------|----------|
| **transaction** | Batch operations | ✅ Yes | Executing multiple operations atomically |
| **batch** | Batch operations | ✅ Yes | Executing multiple operations independently |
| **collection** | Data grouping | ❌ No | Importing/exporting data |
| **document** | Clinical document | ❌ No | Sharing clinical documents |
| **message** | Messaging | ❌ No | FHIR messaging |

Prompt Opinion likely expects **collection** or individual resources for import.

## Next Steps

1. ✅ **DONE**: Converted to collection bundles
2. ⏭️ **TODO**: Upload from `output/fhir_collection/`
3. ⏭️ **TODO**: If still fails, try smaller files
4. ⏭️ **TODO**: If still fails, extract individual resources
5. ⏭️ **TODO**: If still fails, contact Prompt Opinion support

---

**Status**: ✅ Collection bundles ready  
**Location**: `synthea/output/fhir_collection/`  
**Files**: 112 bundles (110 patients)  

Try uploading from the new `fhir_collection` directory!
