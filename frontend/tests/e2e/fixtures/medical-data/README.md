# Medical Imaging Test Data

## Directory Structure

Place your medical image files in the following directories:
- `case-001/`: First medical imaging case (CT scan, NIfTI format)
- `case-002/`: Second medical imaging case

## Supported Formats

- NIfTI (.nii, .nii.gz files) - Primary format
- DICOM (.dcm files) - Legacy support
- CT scans
- X-ray images
- Multi-slice medical imaging data

## After Placing Files

Run the validation script to generate metadata:
```bash
npm run validate-images
```

This will create `metadata.json` with information about your medical image files.

## Expected Structure After Upload

```
medical-data/
├── README.md
├── metadata.json           # Auto-generated
├── case-001/
│   ├── scan.nii.gz        # NIfTI format (recommended)
│   ├── slice-001.dcm      # Or DICOM slices
│   ├── slice-002.dcm
│   └── ...
└── case-002/
    ├── scan.nii.gz
    └── ...
```

## Privacy and Compliance

- Only use anonymized or synthetic medical imaging data for testing
- Do not commit real patient data to version control
- Ensure compliance with HIPAA and other relevant regulations
- Test data should be added to .gitignore (*.nii, *.nii.gz, *.dcm)

## Notes

- The validation tool will automatically scan subdirectories
- Medical image files can have any name (recommended: descriptive names)
- Minimum 1 medical image file per case directory
- Maximum file size: 500MB per file
- NIfTI format is recommended for better performance
