"""
NIfTI file processing utilities for converting NIfTI files to web-viewable images
"""

import os
import io
import base64
from typing import Optional, List, Tuple
from pathlib import Path

try:
    import nibabel as nib
    import numpy as np
    from PIL import Image
    NII_AVAILABLE = True
except ImportError:
    NII_AVAILABLE = False
    print("Warning: NIfTI processing libraries not available. Install nibabel, numpy, and Pillow.")


class NiiProcessor:
    """Handles NIfTI file processing and conversion to web-viewable images"""

    def __init__(self, upload_dir: str = None):
        # Use /tmp for Docker containers or current directory for local development
        if upload_dir is None:
            # Try to use /tmp first (works in Docker), fallback to current directory
            try:
                test_path = Path("/tmp/mendai_uploads")
                test_path.mkdir(exist_ok=True)
                upload_dir = "/tmp/mendai_uploads"
            except PermissionError:
                # Fallback to current directory
                upload_dir = "uploaded_files"
        
        self.upload_dir = Path(upload_dir)
        try:
            self.upload_dir.mkdir(exist_ok=True)
        except PermissionError as e:
            print(f"Warning: Could not create upload directory {self.upload_dir}: {e}")
            # Use /tmp as absolute fallback
            self.upload_dir = Path("/tmp/mendai_uploads")
            self.upload_dir.mkdir(exist_ok=True)
        
        self.converted_dir = self.upload_dir / "converted"
        try:
            self.converted_dir.mkdir(exist_ok=True)
        except PermissionError as e:
            print(f"Warning: Could not create converted directory {self.converted_dir}: {e}")
            # Use /tmp as absolute fallback
            self.converted_dir = Path("/tmp/mendai_converted")
            self.converted_dir.mkdir(exist_ok=True)

    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to disk and return file path"""
        file_path = self.upload_dir / filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return str(file_path)

    def _normalize_slice(self, slice_data: np.ndarray) -> np.ndarray:
        """
        Normalize a single slice to 0-255 range for PNG conversion

        Args:
            slice_data: 2D numpy array representing one slice

        Returns:
            Normalized 2D array as uint8
        """
        # Handle NaN and infinite values
        slice_data = np.nan_to_num(slice_data, nan=0.0, posinf=0.0, neginf=0.0)

        # Normalize to 0-255 range
        slice_min = slice_data.min()
        slice_max = slice_data.max()

        if slice_max > slice_min:
            normalized = ((slice_data - slice_min) / (slice_max - slice_min) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(slice_data, dtype=np.uint8)

        return normalized

    def _resize_image_for_api(self, image: Image.Image, max_dimension: int = 1024) -> Image.Image:
        """
        Resize image to fit within max_dimension while maintaining aspect ratio.
        This reduces token usage for OpenAI Vision API.

        Args:
            image: PIL Image to resize
            max_dimension: Maximum width or height (default 1024)

        Returns:
            Resized PIL Image
        """
        width, height = image.size
        
        # Only resize if image is larger than max_dimension
        if width <= max_dimension and height <= max_dimension:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        
        # Use high-quality resampling for medical images
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def convert_nii_to_png_slices(self, nii_path: str, axis: int = 2) -> List[str]:
        """
        Convert NIfTI file to multiple PNG files (one per slice)

        Args:
            nii_path: Path to the NIfTI file (.nii or .nii.gz)
            axis: Axis along which to slice (0=sagittal, 1=coronal, 2=axial/transverse)
                  Default is 2 (axial), which is the most common view for CT scans

        Returns:
            List of paths to converted PNG files, or empty list if conversion failed
        """
        if not NII_AVAILABLE:
            print("NIfTI processing libraries not available")
            return []

        try:
            # Load NIfTI file
            nii_img = nib.load(nii_path)
            img_data = nii_img.get_fdata()

            print(f"Loaded NIfTI file: {nii_path}, shape: {img_data.shape}, dtype: {img_data.dtype}")

            # Get number of slices along the specified axis
            num_slices = img_data.shape[axis]
            print(f"Extracting {num_slices} slices along axis {axis}")

            png_paths = []
            nii_filename = Path(nii_path).stem.replace('.nii', '')  # Remove .nii extension if present

            # Extract and convert each slice
            for slice_idx in range(num_slices):
                # Extract slice based on axis
                if axis == 0:
                    slice_data = img_data[slice_idx, :, :]
                elif axis == 1:
                    slice_data = img_data[:, slice_idx, :]
                else:  # axis == 2 (default)
                    slice_data = img_data[:, :, slice_idx]

                # Normalize slice to 0-255
                normalized_slice = self._normalize_slice(slice_data)

                # Convert to PIL Image (grayscale)
                image = Image.fromarray(normalized_slice, mode='L')

                # Rotate image 90 degrees counterclockwise and flip for proper orientation
                # This is common for medical images to match radiological conventions
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
                image = image.rotate(90, expand=True)

                # Generate output filename with slice number (zero-padded for sorting)
                png_filename = f"{nii_filename}_slice_{slice_idx:04d}.png"
                png_path = self.converted_dir / png_filename

                # Save as PNG
                image.save(png_path, 'PNG')
                png_paths.append(str(png_path))

            print(f"Successfully converted {nii_path} to {len(png_paths)} PNG slices")
            return png_paths

        except Exception as e:
            print(f"Error converting NIfTI file {nii_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def convert_nii_to_base64_slices(self, nii_path: str, axis: int = 2, max_slices: Optional[int] = None) -> List[str]:
        """
        Convert NIfTI file directly to base64 data URLs for web display (all slices)

        Args:
            nii_path: Path to the NIfTI file
            axis: Axis along which to slice (0=sagittal, 1=coronal, 2=axial)
            max_slices: Maximum number of slices to convert (None for all slices)

        Returns:
            List of base64 data URL strings, or empty list if conversion failed
        """
        if not NII_AVAILABLE:
            print("NIfTI processing libraries not available")
            return []

        try:
            # Load NIfTI file
            nii_img = nib.load(nii_path)
            img_data = nii_img.get_fdata()

            print(f"Loaded NIfTI file: {nii_path}, shape: {img_data.shape}")

            # Get number of slices
            num_slices = img_data.shape[axis]
            if max_slices:
                num_slices = min(num_slices, max_slices)

            print(f"Converting {num_slices} slices to base64 data URLs")

            data_urls = []

            # Convert each slice
            for slice_idx in range(num_slices):
                # Extract slice based on axis
                if axis == 0:
                    slice_data = img_data[slice_idx, :, :]
                elif axis == 1:
                    slice_data = img_data[:, slice_idx, :]
                else:  # axis == 2 (default)
                    slice_data = img_data[:, :, slice_idx]

                # Normalize slice
                normalized_slice = self._normalize_slice(slice_data)

                # Convert to PIL Image
                image = Image.fromarray(normalized_slice, mode='L')

                # Apply proper orientation
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
                image = image.rotate(90, expand=True)

                # Resize image to reduce token usage for OpenAI API
                # 1024x1024 is a good balance between quality and token count
                image = self._resize_image_for_api(image, max_dimension=1024)

                # Convert to base64 using JPEG for better compression
                # JPEG quality 85 provides good quality with much smaller file size than PNG
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=85, optimize=True)
                buffer.seek(0)

                # Create data URL with JPEG format
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                data_url = f"data:image/jpeg;base64,{img_base64}"
                data_urls.append(data_url)

            print(f"Successfully converted {nii_path} to {len(data_urls)} base64 data URLs")
            return data_urls

        except Exception as e:
            print(f"Error converting NIfTI file {nii_path} to base64: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_nii_info(self, nii_path: str) -> dict:
        """
        Extract metadata from NIfTI file

        Args:
            nii_path: Path to the NIfTI file

        Returns:
            Dictionary containing NIfTI metadata
        """
        if not NII_AVAILABLE:
            return {"error": "NIfTI processing libraries not available"}

        try:
            # Load NIfTI file
            nii_img = nib.load(nii_path)
            img_data = nii_img.get_fdata()
            header = nii_img.header

            info = {
                "file_path": nii_path,
                "shape": str(img_data.shape),
                "dimensions": f"{img_data.shape[0]}x{img_data.shape[1]}x{img_data.shape[2]}",
                "num_slices": {
                    "sagittal": img_data.shape[0],
                    "coronal": img_data.shape[1],
                    "axial": img_data.shape[2]
                },
                "data_type": str(img_data.dtype),
                "voxel_size": str(header.get_zooms()[:3]),  # mm per voxel
                "affine_matrix": str(nii_img.affine.tolist()),
                "file_size_mb": round(Path(nii_path).stat().st_size / (1024 * 1024), 2)
            }

            # Additional metadata if available
            if hasattr(header, 'get_xyzt_units'):
                units = header.get_xyzt_units()
                info["spatial_unit"] = str(units[0])
                info["temporal_unit"] = str(units[1])

            return info

        except Exception as e:
            return {"error": f"Error reading NIfTI metadata: {str(e)}"}


# Global instance
nii_processor = NiiProcessor()
