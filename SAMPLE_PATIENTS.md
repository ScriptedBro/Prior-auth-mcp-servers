# Sample Patients for Testing

The following patients are loaded in the FHIR server and ready for prior authorization testing.

## Quick Reference

| Patient ID | Name | Gender | Birth Date | Age |
|------------|------|--------|------------|-----|
| 64513 | Ramiro608 Considine820 | Male | 1954-10-03 | 71 |
| 67237 | Rema399 Crist667 | Female | 2023-11-27 | 2 |
| 67433 | Roscoe437 Osinski784 | Male | 1980-08-12 | 45 |
| 67960 | Rufus33 Tromp100 | Male | 1954-10-03 | 71 |
| 75075 | Sanda877 Runolfsson901 | Female | 1998-10-07 | 27 |
| 75813 | Santiago500 Kub800 | Male | 2014-01-31 | 12 |
| 76243 | Santiago500 Nájera755 | Male | 1992-01-19 | 34 |
| 76456 | Sara501 Vélez150 | Female | 2000-08-27 | 25 |
| 77433 | Seymour882 Hermann103 | Male | 1954-10-03 | 71 |
| 78211 | Shasta644 Johns824 | Female | 1960-09-01 | 65 |

## Detailed Patient Information

### Patient 1: Ramiro608 Considine820
- **FHIR ID**: `64513`
- **Gender**: Male
- **Birth Date**: 1954-10-03 (Age 71)
- **Use Cases**: Elderly patient, likely has chronic conditions suitable for testing medication prior auths

### Patient 2: Rema399 Crist667
- **FHIR ID**: `67237`
- **Gender**: Female
- **Birth Date**: 2023-11-27 (Age 2)
- **Use Cases**: Pediatric patient, good for testing pediatric medication/procedure auths

### Patient 3: Roscoe437 Osinski784
- **FHIR ID**: `67433`
- **Gender**: Male
- **Birth Date**: 1980-08-12 (Age 45)
- **Use Cases**: Middle-aged adult, suitable for testing various procedures and specialist referrals

### Patient 4: Rufus33 Tromp100
- **FHIR ID**: `67960`
- **Gender**: Male
- **Birth Date**: 1954-10-03 (Age 71)
- **Use Cases**: Elderly patient, good for testing complex medication regimens

### Patient 5: Sanda877 Runolfsson901
- **FHIR ID**: `75075`
- **Gender**: Female
- **Birth Date**: 1998-10-07 (Age 27)
- **Use Cases**: Young adult, suitable for testing preventive care and specialist referrals

### Patient 6: Santiago500 Kub800
- **FHIR ID**: `75813`
- **Gender**: Male
- **Birth Date**: 2014-01-31 (Age 12)
- **Use Cases**: Adolescent patient, good for testing pediatric specialist referrals

### Patient 7: Santiago500 Nájera755
- **FHIR ID**: `76243`
- **Gender**: Male
- **Birth Date**: 1992-01-19 (Age 34)
- **Use Cases**: Adult patient, suitable for testing imaging procedures (MRI, CT)

### Patient 8: Sara501 Vélez150
- **FHIR ID**: `76456`
- **Gender**: Female
- **Birth Date**: 2000-08-27 (Age 25)
- **Use Cases**: Young adult female, good for testing various procedures

### Patient 9: Seymour882 Hermann103
- **FHIR ID**: `77433`
- **Gender**: Male
- **Birth Date**: 1954-10-03 (Age 71)
- **Use Cases**: Elderly patient with likely multiple comorbidities

### Patient 10: Shasta644 Johns824
- **FHIR ID**: `78211`
- **Gender**: Female
- **Birth Date**: 1960-09-01 (Age 65)
- **Use Cases**: Senior patient, suitable for testing Medicare-related authorizations

## Testing Scenarios

### Scenario 1: MRI Prior Authorization
**Patient**: 67433 (Roscoe, 45M)
**Request**: "Submit prior auth for MRI lumbar spine for patient 67433, insurance Blue Cross Blue Shield"
**Expected**: Agent checks BCBS requirements, gathers patient conditions, drafts authorization

### Scenario 2: Specialist Referral
**Patient**: 75075 (Sanda, 27F)
**Request**: "Prior auth for cardiology referral for patient 75075, UnitedHealthcare"
**Expected**: Agent checks if referral requires auth, gathers relevant cardiac history

### Scenario 3: Medication Prior Auth
**Patient**: 64513 (Ramiro, 71M)
**Request**: "Submit prior auth for Humira for patient 64513, Blue Cross Blue Shield"
**Expected**: Agent checks medication requirements, verifies diagnosis, checks for failed DMARDs

### Scenario 4: CT Scan Authorization
**Patient**: 76243 (Santiago, 34M)
**Request**: "Prior auth for CT scan abdomen for patient 76243, Aetna"
**Expected**: Agent checks Aetna requirements, gathers clinical indication

### Scenario 5: Appeal Generation
**Patient**: 67433 (Roscoe, 45M)
**Request**: "Appeal denied MRI auth for patient 67433, denied for 'insufficient conservative treatment'"
**Expected**: Agent generates appeal letter with evidence of conservative treatments

## How to Query Patient Data

### Get Patient Demographics
```bash
curl "http://localhost:8080/fhir/Patient/64513"
```

### Get Patient Conditions
```bash
curl "http://localhost:8080/fhir/Condition?patient=64513"
```

### Get Patient Medications
```bash
curl "http://localhost:8080/fhir/MedicationRequest?patient=64513"
```

### Get Patient Procedures
```bash
curl "http://localhost:8080/fhir/Procedure?patient=64513"
```

### Get Patient Observations (Labs)
```bash
curl "http://localhost:8080/fhir/Observation?patient=64513&category=laboratory"
```

## Using with MCP Servers

### Patient Records MCP
```json
{
  "tool": "get_prior_auth_summary",
  "arguments": {
    "patient_id": "64513"
  }
}
```

### Payer Rules MCP
```json
{
  "tool": "get_auth_criteria",
  "arguments": {
    "payer": "Blue Cross Blue Shield",
    "procedure_or_medication": "MRI"
  }
}
```

## Notes

- All patients have synthetic data generated by Synthea
- Data includes realistic medical histories, conditions, medications, and procedures
- FHIR server is running at: `http://localhost:8080/fhir`
- Total patients loaded: **39**
- All data is HIPAA-compliant synthetic data (not real patients)
