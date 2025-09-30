#!/usr/bin/env python3
"""
Test script to verify DICOM conversion is working
"""

import os
import sys
import numpy as np
from pathlib import Path

# Add the engine path to import our modules
sys.path.append('/app')
from engine.utils.dicom_processor import dicom_processor

def create_sample_dicom():
    """Create a simple test DICOM file"""
    try:
        import pydicom
        from pydicom.dataset import Dataset, FileDataset
        from pydicom.uid import ExplicitVRLittleEndian
        import tempfile

        # Create a simple test image (100x100 pixels)
        test_image = np.random.randint(0, 255, (100, 100), dtype=np.uint16)

        # Create DICOM dataset
        ds = Dataset()
        ds.PatientName = "Test^Patient"
        ds.PatientID = "12345"
        ds.Modality = "CT"
        ds.StudyInstanceUID = "1.2.3.4.5.6.7.8.9"
        ds.SeriesInstanceUID = "1.2.3.4.5.6.7.8.9.1"
        ds.SOPInstanceUID = "1.2.3.4.5.6.7.8.9.1.1"
        ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
        ds.Rows = 100
        ds.Columns = 100
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 0
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelData = test_image.tobytes()

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.dcm', delete=False)
        temp_file.close()

        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = ds.SOPClassUID
        file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

        file_ds = FileDataset(temp_file.name, ds, file_meta=file_meta, preamble=b'\x00' * 128)
        file_ds.save_as(temp_file.name)

        return temp_file.name

    except Exception as e:
        print(f"Error creating sample DICOM: {e}")
        return None

def test_conversion():
    """Test DICOM to image conversion"""
    print("=== Testing DICOM Conversion ===")

    # Create sample DICOM
    dicom_path = create_sample_dicom()
    if not dicom_path:
        print("❌ Failed to create sample DICOM")
        return False

    print(f"✅ Created sample DICOM: {dicom_path}")

    # Test conversion to base64
    print("Testing conversion to base64...")
    base64_result = dicom_processor.convert_dicom_to_base64(dicom_path)

    if base64_result:
        print(f"✅ Conversion successful! Image size: {len(base64_result)} characters")
        print(f"Image preview: {base64_result[:100]}...")

        # Clean up
        os.unlink(dicom_path)
        return True
    else:
        print("❌ Conversion failed")
        os.unlink(dicom_path)
        return False

if __name__ == "__main__":
    success = test_conversion()
    if success:
        print("\n🎉 DICOM conversion system is working!")
    else:
        print("\n❌ DICOM conversion system needs debugging")