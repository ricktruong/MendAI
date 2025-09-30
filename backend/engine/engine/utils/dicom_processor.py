"""
DICOM file processing utilities for converting DICOM files to web-viewable images
"""

import os
import io
import base64
from typing import Optional, Tuple
from pathlib import Path

try:
    import pydicom
    import numpy as np
    from PIL import Image
    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False
    print("Warning: DICOM processing libraries not available. Install pydicom, numpy, and Pillow.")


class DicomProcessor:
    """Handles DICOM file processing and conversion to web-viewable images"""

    def __init__(self, upload_dir: str = "uploaded_files"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.converted_dir = self.upload_dir / "converted"
        self.converted_dir.mkdir(exist_ok=True)

    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to disk and return file path"""
        file_path = self.upload_dir / filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return str(file_path)

    def convert_dicom_to_png(self, dicom_path: str) -> Optional[str]:
        """
        Convert DICOM file to PNG format

        Args:
            dicom_path: Path to the DICOM file

        Returns:
            Path to converted PNG file, or None if conversion failed
        """
        if not DICOM_AVAILABLE:
            print("DICOM processing libraries not available")
            return None

        try:
            # Read DICOM file - try with force=True if normal reading fails
            try:
                dicom_data = pydicom.dcmread(dicom_path)
            except Exception as e:
                print(f"Standard DICOM read failed, trying with force=True: {str(e)}")
                dicom_data = pydicom.dcmread(dicom_path, force=True)

            # Get pixel array
            pixel_array = dicom_data.pixel_array

            # Handle different bit depths and normalize to 0-255
            if pixel_array.dtype != np.uint8:
                # Normalize to 0-255 range
                pixel_min = pixel_array.min()
                pixel_max = pixel_array.max()
                if pixel_max > pixel_min:
                    pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
                else:
                    pixel_array = np.zeros_like(pixel_array, dtype=np.uint8)

            # Handle windowing if available
            if hasattr(dicom_data, 'WindowCenter') and hasattr(dicom_data, 'WindowWidth'):
                center = float(dicom_data.WindowCenter)
                width = float(dicom_data.WindowWidth)

                # Apply windowing
                img_min = center - width // 2
                img_max = center + width // 2
                pixel_array = np.clip(pixel_array, img_min, img_max)
                pixel_array = ((pixel_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)

            # Convert to PIL Image
            if len(pixel_array.shape) == 2:
                # Grayscale image
                image = Image.fromarray(pixel_array, mode='L')
            elif len(pixel_array.shape) == 3:
                # Color image
                image = Image.fromarray(pixel_array, mode='RGB')
            else:
                print(f"Unsupported image shape: {pixel_array.shape}")
                return None

            # Generate output filename
            dicom_filename = Path(dicom_path).stem
            png_filename = f"{dicom_filename}.png"
            png_path = self.converted_dir / png_filename

            # Save as PNG
            image.save(png_path, 'PNG')

            print(f"Successfully converted {dicom_path} to {png_path}")
            return str(png_path)

        except Exception as e:
            print(f"Error converting DICOM file {dicom_path}: {str(e)}")
            return None

    def convert_dicom_to_base64(self, dicom_path: str) -> Optional[str]:
        """
        Convert DICOM file directly to base64 data URL for web display

        Args:
            dicom_path: Path to the DICOM file

        Returns:
            Base64 data URL string, or None if conversion failed
        """
        if not DICOM_AVAILABLE:
            print("DICOM processing libraries not available")
            return None

        try:
            # Read DICOM file - try with force=True if normal reading fails
            try:
                dicom_data = pydicom.dcmread(dicom_path)
            except Exception as e:
                print(f"Standard DICOM read failed, trying with force=True: {str(e)}")
                dicom_data = pydicom.dcmread(dicom_path, force=True)

            # Get pixel array
            pixel_array = dicom_data.pixel_array

            # Handle different bit depths and normalize to 0-255
            if pixel_array.dtype != np.uint8:
                # Normalize to 0-255 range
                pixel_min = pixel_array.min()
                pixel_max = pixel_array.max()
                if pixel_max > pixel_min:
                    pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
                else:
                    pixel_array = np.zeros_like(pixel_array, dtype=np.uint8)

            # Handle windowing if available for better contrast
            if hasattr(dicom_data, 'WindowCenter') and hasattr(dicom_data, 'WindowWidth'):
                try:
                    center = float(dicom_data.WindowCenter)
                    width = float(dicom_data.WindowWidth)

                    # Apply windowing
                    img_min = center - width // 2
                    img_max = center + width // 2
                    pixel_array = np.clip(pixel_array, img_min, img_max)
                    pixel_array = ((pixel_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)
                except:
                    # If windowing fails, continue with normalized data
                    pass

            # Convert to PIL Image
            if len(pixel_array.shape) == 2:
                # Grayscale image
                image = Image.fromarray(pixel_array, mode='L')
            elif len(pixel_array.shape) == 3:
                # Color image
                image = Image.fromarray(pixel_array, mode='RGB')
            else:
                print(f"Unsupported image shape: {pixel_array.shape}")
                return None

            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)

            # Create data URL
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            data_url = f"data:image/png;base64,{img_base64}"

            print(f"Successfully converted {dicom_path} to base64 data URL")
            return data_url

        except Exception as e:
            print(f"Error converting DICOM file {dicom_path} to base64: {str(e)}")
            return None

    def get_dicom_info(self, dicom_path: str) -> dict:
        """
        Extract metadata from DICOM file

        Args:
            dicom_path: Path to the DICOM file

        Returns:
            Dictionary containing DICOM metadata
        """
        if not DICOM_AVAILABLE:
            return {"error": "DICOM processing libraries not available"}

        try:
            # Read DICOM file - try with force=True if normal reading fails
            try:
                dicom_data = pydicom.dcmread(dicom_path)
            except Exception as e:
                print(f"Standard DICOM read failed, trying with force=True: {str(e)}")
                dicom_data = pydicom.dcmread(dicom_path, force=True)

            info = {
                "patient_name": str(getattr(dicom_data, 'PatientName', 'Unknown')),
                "patient_id": str(getattr(dicom_data, 'PatientID', 'Unknown')),
                "study_date": str(getattr(dicom_data, 'StudyDate', 'Unknown')),
                "modality": str(getattr(dicom_data, 'Modality', 'Unknown')),
                "series_description": str(getattr(dicom_data, 'SeriesDescription', 'Unknown')),
                "image_size": f"{dicom_data.pixel_array.shape[1]}x{dicom_data.pixel_array.shape[0]}",
                "bits_allocated": getattr(dicom_data, 'BitsAllocated', 'Unknown'),
                "pixel_spacing": str(getattr(dicom_data, 'PixelSpacing', 'Unknown')),
            }

            return info

        except Exception as e:
            return {"error": f"Error reading DICOM metadata: {str(e)}"}


# Global instance
dicom_processor = DicomProcessor()