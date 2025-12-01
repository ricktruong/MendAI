/**
 * Medical Image File Validation Tool
 * Supports both DICOM (.dcm) and NIfTI (.nii, .nii.gz) formats
 */

const fs = require('fs');
const path = require('path');

class MedicalImageValidator {
  constructor(dataDir) {
    this.dataDir = dataDir;
    this.cases = [];
  }

  /**
   * Scan all medical image files in the test data directory
   */
  scanMedicalImages() {
    console.log('Scanning medical image test data...\n');

    const caseDirs = ['case-001', 'case-002'];

    caseDirs.forEach(caseDir => {
      const fullPath = path.join(this.dataDir, caseDir);

      if (!fs.existsSync(fullPath)) {
        console.warn(`Warning: Directory ${caseDir} does not exist`);
        return;
      }

      const files = this.scanDirectory(fullPath);
      const imageFiles = files.filter(f => this.isMedicalImageFile(f));

      const caseData = {
        case_id: caseDir.split('-')[1],
        directory: caseDir,
        file_count: imageFiles.length,
        files: imageFiles.map(f => path.basename(f)),
        metadata: this.extractBasicMetadata(fullPath, imageFiles)
      };

      this.cases.push(caseData);

      console.log(`[${caseDir}] Found ${imageFiles.length} medical image files`);
    });
  }

  /**
   * Recursively scan directory for files
   */
  scanDirectory(dir) {
    let results = [];

    try {
      const files = fs.readdirSync(dir);

      files.forEach(file => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);

        if (stat.isDirectory()) {
          // Recursively scan subdirectories
          results = results.concat(this.scanDirectory(filePath));
        } else if (stat.isFile()) {
          results.push(filePath);
        }
      });
    } catch (error) {
      console.error(`Error scanning directory ${dir}:`, error.message);
    }

    return results;
  }

  /**
   * Check if file is a medical image file (DICOM or NIfTI)
   */
  isMedicalImageFile(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const basename = path.basename(filePath).toLowerCase();

    // Check for NIfTI formats
    if (ext === '.nii' || basename.endsWith('.nii.gz')) {
      return true;
    }

    // Check for DICOM formats
    if (ext === '.dcm' || ext === '.dicom') {
      return true;
    }

    // Check for DICOM file signature
    try {
      const buffer = Buffer.alloc(132);
      const fd = fs.openSync(filePath, 'r');
      fs.readSync(fd, buffer, 0, 132, 0);
      fs.closeSync(fd);

      // Check for DICM signature at offset 128
      if (buffer.slice(128, 132).toString() === 'DICM') {
        return true;
      }
    } catch (error) {
      // Not a DICOM file or cannot read
    }

    return false;
  }

  /**
   * Detect file format
   */
  detectFormat(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const basename = path.basename(filePath).toLowerCase();

    if (ext === '.nii' || basename.endsWith('.nii.gz')) {
      return 'NIfTI';
    }

    if (ext === '.dcm' || ext === '.dicom') {
      return 'DICOM';
    }

    // Check DICOM signature
    try {
      const buffer = Buffer.alloc(132);
      const fd = fs.openSync(filePath, 'r');
      fs.readSync(fd, buffer, 0, 132, 0);
      fs.closeSync(fd);

      if (buffer.slice(128, 132).toString() === 'DICM') {
        return 'DICOM';
      }
    } catch (error) {
      // Ignore
    }

    return 'Unknown';
  }

  /**
   * Validate medical image file format
   */
  validateFile(filePath) {
    try {
      const stats = fs.statSync(filePath);

      // Basic validation
      if (stats.size === 0) {
        return { valid: false, error: 'File is empty' };
      }

      if (stats.size > 500 * 1024 * 1024) {
        return { valid: false, error: 'File exceeds 500MB limit' };
      }

      const format = this.detectFormat(filePath);
      if (format === 'Unknown') {
        return { valid: false, error: 'Unknown medical image format' };
      }

      return { valid: true, format };
    } catch (error) {
      return { valid: false, error: error.message };
    }
  }

  /**
   * Extract basic metadata from medical image files
   */
  extractBasicMetadata(dirPath, files) {
    const metadata = {
      patient_id: null,
      modality: null,
      format: null,
      body_part: null,
      slice_thickness: null,
      study_date: null,
      study_description: null,
      total_size_mb: 0
    };

    // Calculate total size
    let totalSize = 0;
    files.forEach(file => {
      try {
        const stats = fs.statSync(file);
        totalSize += stats.size;
      } catch (error) {
        // Ignore
      }
    });

    metadata.total_size_mb = (totalSize / (1024 * 1024)).toFixed(2);

    // Detect format from first file
    if (files.length > 0) {
      metadata.format = this.detectFormat(files[0]);

      const firstFile = path.basename(files[0]);
      const upperName = firstFile.toUpperCase();

      // Try to detect modality from filename
      if (upperName.includes('CT')) {
        metadata.modality = 'CT';
      } else if (upperName.includes('MR') || upperName.includes('MRI')) {
        metadata.modality = 'MR';
      } else if (upperName.includes('CR') || upperName.includes('DX')) {
        metadata.modality = 'CR/DX';
      } else if (upperName.includes('PET')) {
        metadata.modality = 'PET';
      }

      // Check for body part indicators
      if (upperName.includes('CHEST')) {
        metadata.body_part = 'CHEST';
      } else if (upperName.includes('HEAD') || upperName.includes('BRAIN')) {
        metadata.body_part = 'HEAD';
      } else if (upperName.includes('ABDOMEN')) {
        metadata.body_part = 'ABDOMEN';
      }
    }

    return metadata;
  }

  /**
   * Generate metadata report
   */
  generateMetadataReport() {
    this.scanMedicalImages();

    const report = {
      generated_at: new Date().toISOString(),
      version: '1.0',
      tool: 'MendAI Medical Image Validator',
      cases: this.cases
    };

    // Save to metadata.json
    const outputPath = path.join(this.dataDir, 'metadata.json');
    fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));

    console.log('\n' + '='.repeat(50));
    console.log('Medical Image Validation Summary');
    console.log('='.repeat(50));
    console.log(`Total Cases: ${this.cases.length}`);

    let totalFiles = 0;
    this.cases.forEach(caseData => {
      totalFiles += caseData.file_count;
      console.log(`\nCase ${caseData.case_id}:`);
      console.log(`  Files: ${caseData.file_count}`);
      console.log(`  Size: ${caseData.metadata.total_size_mb} MB`);
      console.log(`  Format: ${caseData.metadata.format || 'Unknown'}`);
      console.log(`  Modality: ${caseData.metadata.modality || 'Unknown'}`);
      console.log(`  Body Part: ${caseData.metadata.body_part || 'Unknown'}`);
    });

    console.log(`\nTotal Medical Image Files: ${totalFiles}`);
    console.log(`\nMetadata saved to: ${outputPath}`);
    console.log('='.repeat(50) + '\n');

    // Warnings
    if (totalFiles === 0) {
      console.warn('WARNING: No medical image files found!');
      console.warn('Please place your medical image files (.nii, .dcm) in case-001/ and case-002/ directories.');
    }

    return report;
  }

  /**
   * Validate all files and report issues
   */
  validateAll() {
    console.log('\nValidating medical image files...\n');

    let issueCount = 0;

    this.cases.forEach(caseData => {
      const caseDir = path.join(this.dataDir, caseData.directory);

      caseData.files.forEach(file => {
        const filePath = path.join(caseDir, file);
        const validation = this.validateFile(filePath);

        if (!validation.valid) {
          console.error(`[ERROR] ${file}: ${validation.error}`);
          issueCount++;
        }
      });
    });

    if (issueCount === 0) {
      console.log('All medical image files passed validation!\n');
    } else {
      console.warn(`\nFound ${issueCount} validation issues.\n`);
    }
  }
}

// Main execution
function main() {
  const dataDir = path.join(__dirname, 'medical-data');

  console.log('\n' + '='.repeat(50));
  console.log('MendAI Medical Image Validation Tool');
  console.log('Supports: DICOM (.dcm) and NIfTI (.nii)');
  console.log('='.repeat(50) + '\n');

  if (!fs.existsSync(dataDir)) {
    console.error('Error: medical-data directory not found!');
    console.error('Expected path:', dataDir);
    process.exit(1);
  }

  const validator = new MedicalImageValidator(dataDir);

  try {
    const report = validator.generateMetadataReport();
    validator.validateAll();

    console.log('Validation complete!');
    process.exit(0);
  } catch (error) {
    console.error('\nValidation failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { MedicalImageValidator };
