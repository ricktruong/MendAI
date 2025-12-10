#!/usr/bin/env python3
"""
Utility script to downsample NIfTI files by keeping every Nth slice.
This reduces file size significantly for demo purposes.

Usage:
    python scripts/downsample_nii.py input.nii output.nii [--axis 2] [--step 2]
    
    --axis: Which axis to downsample (0=sagittal, 1=coronal, 2=axial, default=2)
    --step: Keep every Nth slice (default=2, i.e., keep every other slice)
    
Example:
    # Reduce to half the slices (keep every other slice)
    python scripts/downsample_nii.py scan.nii scan_half.nii
    
    # Reduce to quarter (keep every 4th slice)
    python scripts/downsample_nii.py scan.nii scan_quarter.nii --step 4
"""

import argparse
import sys
from pathlib import Path

try:
    import nibabel as nib
    import numpy as np
except ImportError:
    print("Error: nibabel and numpy are required. Install with:")
    print("  pip install nibabel numpy")
    sys.exit(1)


def downsample_nii(input_path: str, output_path: str, axis: int = 2, step: int = 2):
    """
    Downsample a NIfTI file by keeping every Nth slice along the specified axis.
    
    Args:
        input_path: Path to input .nii or .nii.gz file
        output_path: Path to output .nii file
        axis: Which axis to downsample (0=sagittal, 1=coronal, 2=axial)
        step: Keep every Nth slice (2 = keep every other slice = 50% reduction)
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Load the NIfTI file
    print(f"Loading: {input_path}")
    nii_img = nib.load(str(input_file))
    img_data = nii_img.get_fdata()
    
    original_shape = img_data.shape
    print(f"Original shape: {original_shape}")
    print(f"Original size: {input_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Downsample along the specified axis
    if axis == 0:
        # Sagittal: keep every Nth slice in first dimension
        downsampled_data = img_data[::step, :, :]
    elif axis == 1:
        # Coronal: keep every Nth slice in second dimension
        downsampled_data = img_data[:, ::step, :]
    else:  # axis == 2 (axial, most common for CT scans)
        # Axial: keep every Nth slice in third dimension
        downsampled_data = img_data[:, :, ::step]
    
    new_shape = downsampled_data.shape
    reduction = (1 - (new_shape[axis] / original_shape[axis])) * 100
    
    print(f"New shape: {new_shape}")
    print(f"Reduction: {reduction:.1f}% ({original_shape[axis]} → {new_shape[axis]} slices)")
    
    # Create new NIfTI image with same affine and header
    # Adjust the affine matrix to account for the slice spacing change
    new_affine = nii_img.affine.copy()
    new_affine[:3, axis] = new_affine[:3, axis] * step  # Scale spacing
    
    new_nii = nib.Nifti1Image(downsampled_data, new_affine, nii_img.header)
    
    # Save the downsampled file
    print(f"Saving: {output_path}")
    nib.save(new_nii, str(output_file))
    
    new_size = output_file.stat().st_size / (1024*1024)
    size_reduction = (1 - (new_size / (input_file.stat().st_size / (1024*1024)))) * 100
    
    print(f"New file size: {new_size:.2f} MB")
    print(f"Size reduction: {size_reduction:.1f}%")
    print(f"✓ Successfully created downsampled file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Downsample NIfTI files by keeping every Nth slice",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reduce to half (keep every other slice)
  python scripts/downsample_nii.py scan.nii scan_half.nii
  
  # Reduce to quarter (keep every 4th slice)
  python scripts/downsample_nii.py scan.nii scan_quarter.nii --step 4
  
  # Downsample along sagittal axis
  python scripts/downsample_nii.py scan.nii scan_downsampled.nii --axis 0
        """
    )
    
    parser.add_argument("input", help="Input .nii or .nii.gz file path")
    parser.add_argument("output", help="Output .nii file path")
    parser.add_argument(
        "--axis",
        type=int,
        default=2,
        choices=[0, 1, 2],
        help="Axis to downsample: 0=sagittal, 1=coronal, 2=axial (default: 2)"
    )
    parser.add_argument(
        "--step",
        type=int,
        default=2,
        help="Keep every Nth slice (default: 2, i.e., every other slice = 50%% reduction)"
    )
    
    args = parser.parse_args()
    
    if args.step < 2:
        print("Error: --step must be >= 2")
        sys.exit(1)
    
    downsample_nii(args.input, args.output, args.axis, args.step)


if __name__ == "__main__":
    main()
