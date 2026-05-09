# Upload Cleaned FHIR Data to Prompt Opinion

## Quick Start

Your cleaned FHIR data is ready to upload! Follow these steps:

### Step 1: Locate Your Cleaned Files

```bash
cd ~/Desktop/Health\ Hackathon/synthea/output/fhir_clean/
ls -lh
# You should see 112 JSON files
```

### Step 2: Upload to Prompt Opinion

1. **Open Prompt Opinion** in your browser
2. **Navigate to Patient Data Import**:
   - Look for "FHIR Data" or "Import" section
   - Or go to Settings → Data Import
3. **Click "Upload FHIR Bundle"** or similar button
4. **Select Files**:
   - Browse to `synthea/output/fhir_clean/`
   - You can upload multiple files at once
   - Start with 1-2 files to test, then upload all 110 patient files
5. **Click "Import"** or "Upload"
6. **Wait for Processing**:
   - Prompt Opinion will validate and import the bundles
   - This may take a few minutes for all 112 files

### Step 3: Verify Import Success

After upload, verify:
- ✅ No "conditional reference not found" errors
- ✅ Patients appear in Prompt Opinion's patient list
- ✅ You can view patient demographics
- ✅ You can see conditions, medications, procedures

## What to Upload

### Patient Files (110 files)
Upload all patient bundle files. Each contains:
- Patient demographics
- Medical history (conditions, procedures)
- Medications
- Lab results
- Encounters

**Example files**:
- `Aaron697_Kihn564_3ea65e25-138a-274e-6448-a79905083f22.json`
- `Alden634_O'Reilly797_8b97df74-a4db-a2d6-01f8-0bdbc4e8c736.json`
- etc.

### Skip These Files (2 files)
These files are now empty after cleaning:
- ❌ `hospitalInformation1776252667354.json` (0 entries)
- ❌ `practitionerInformation1776252667354.json` (0 entries)

## Troubleshooting

### Error: "Conditional reference not found"

If you still see this error:

1. **Check which resource** is causing the error (Practitioner? Location? Organization?)
2. **Verify you're uploading from the cleaned directory**:
   ```bash
   # WRONG - original data
   synthea/output/fhir/
   
   # RIGHT - cleaned data
   synthea/output/fhir_clean/
   ```
3. **Re-run the cleaning script**:
   ```bash
   cd synthea
   python3 clean-fhir-for-prompt-opinion.py
   ```

### Error: "Invalid FHIR bundle"

This usually means:
- File is corrupted
- File is not valid JSON
- File is not a FHIR bundle

**Solution**: Skip that file and try others. Most files should work.

### Error: "Duplicate patient ID"

If you've already uploaded some patients:
- Prompt Opinion may reject duplicates
- This is normal - just skip files you've already uploaded

### Upload is Slow

For 110+ files:
- Upload in batches (10-20 files at a time)
- Or use Prompt Opinion's bulk import API if available

## After Upload

### Test Patient Data Access

1. **Open a patient record** in Prompt Opinion
2. **Verify you can see**:
   - Patient name, DOB, gender
   - Conditions (diagnoses)
   - Medications
   - Procedures
   - Lab results

### Configure MCP Servers

Once data is uploaded, configure your MCP servers to use Prompt Opinion's FHIR:

1. **Get FHIR Server URL** from Prompt Opinion settings
2. **Get OAuth credentials** (if required)
3. **Update MCP server environment variables**:
   ```bash
   export FHIR_BASE_URL="https://fhir.promptopinion.ai/..."
   export FHIR_ACCESS_TOKEN="your-token-here"
   ```

### Test MCP Tools

Test that your MCP servers can access the uploaded data:

```bash
# Start MCP servers
cd prior-auth-agent
bash scripts/start-mcp-http.sh

# Test patient records MCP
curl -X POST http://localhost:9002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "list_patients",
      "arguments": {}
    }
  }'
```

## Sample Patients

After upload, you'll have 110 patients with various conditions. Here are some interesting ones:

### Patients with Chronic Conditions
- **Ed239_Ward668**: 11,438 entries (complex medical history)
- **Tonia627_Marquita692_Schiller186**: 12,685 entries (very complex)
- **Rufus33_Tromp100**: 7,115 entries (extensive history)

### Patients with Specific Conditions
See `prior-auth-agent/SAMPLE_PATIENTS.md` for detailed patient profiles including:
- Diabetes patients
- Hypertension patients
- Asthma patients
- Patients needing imaging (MRI, CT)
- Patients on specialty medications

## Next Steps

After successful upload:

1. ✅ **Data uploaded** to Prompt Opinion
2. ⏭️ **Configure MCP servers** with Prompt Opinion FHIR URL
3. ⏭️ **Test MCP tools** with real patient data
4. ⏭️ **Create prior auth agent** in Prompt Opinion
5. ⏭️ **Test complete workflow**:
   - Select a patient
   - Request prior auth for a procedure/medication
   - Agent fetches patient data via MCP
   - Agent checks payer rules via MCP
   - Agent generates auth request via MCP
   - Review generated document

## Support

If you encounter issues:

1. **Check Prompt Opinion documentation**: https://docs.promptopinion.ai/
2. **Verify FHIR data format**: Use FHIR validator
3. **Check cleaned data**: Verify no problematic references remain
4. **Re-run cleaning script**: If needed

---

**Your data is ready! Start uploading to Prompt Opinion now.** 🚀
