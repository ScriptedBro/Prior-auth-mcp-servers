#!/bin/bash
# Upload Synthea-generated FHIR bundles to HAPI FHIR server

FHIR_SERVER="${FHIR_SERVER:-http://localhost:8080/fhir}"
SYNTHEA_OUTPUT="${SYNTHEA_OUTPUT:-../../synthea/output/fhir}"

echo "Uploading Synthea FHIR bundles to $FHIR_SERVER"
echo "Source directory: $SYNTHEA_OUTPUT"
echo ""

# Counter for tracking uploads
SUCCESS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0

# Upload each FHIR bundle
for file in "$SYNTHEA_OUTPUT"/*.json; do
    if [ -f "$file" ]; then
        TOTAL_COUNT=$((TOTAL_COUNT + 1))
        filename=$(basename "$file")
        
        echo -n "Uploading $filename... "
        
        # POST the bundle to the FHIR server
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/fhir+json" \
            -d @"$file" \
            "$FHIR_SERVER" 2>&1)
        
        http_code=$(echo "$response" | tail -n1)
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            echo "✓ Success (HTTP $http_code)"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "✗ Failed (HTTP $http_code)"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
        
        # Small delay to avoid overwhelming the server
        sleep 0.1
    fi
done

echo ""
echo "========================================="
echo "Upload Summary:"
echo "  Total files: $TOTAL_COUNT"
echo "  Successful:  $SUCCESS_COUNT"
echo "  Failed:      $FAIL_COUNT"
echo "========================================="

# Verify data was uploaded
echo ""
echo "Verifying uploaded data..."
patient_count=$(curl -s "$FHIR_SERVER/Patient?_summary=count" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')
echo "Total patients in FHIR server: $patient_count"
