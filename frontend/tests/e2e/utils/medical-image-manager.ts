/**
 * Medical Image Test Data Manager
 * Manages medical image test files (NIfTI, DICOM) and metadata for E2E tests
 */

import * as fs from 'fs';
import * as path from 'path';

export interface CaseMetadata {
  case_id: string;
  directory: string;
  file_count: number;
  files: string[];
  metadata: {
    patient_id: string | null;
    modality: string | null;
    body_part: string | null;
    slice_thickness: string | null;
    study_date: string | null;
    study_description: string | null;
    total_size_mb?: string;
  };
}

export interface MedicalImageMetadata {
  generated_at: string;
  version: string;
  tool?: string;
  cases: CaseMetadata[];
}

/**
 * Medical Image Test Data Manager
 */
export class MedicalImageManager {
  private metadataPath: string;
  private metadata: MedicalImageMetadata | null = null;
  private baseDir: string;

  constructor(metadataPath: string) {
    this.metadataPath = metadataPath;
    this.baseDir = path.dirname(metadataPath);
    this.loadMetadata();
  }

  /**
   * Load metadata from JSON file
   */
  private loadMetadata(): void {
    try {
      if (!fs.existsSync(this.metadataPath)) {
        throw new Error(
          `Metadata file not found: ${this.metadataPath}\n` +
          'Please run "npm run validate-images" to generate metadata'
        );
      }

      const content = fs.readFileSync(this.metadataPath, 'utf-8');
      this.metadata = JSON.parse(content);

      console.log('[MedicalImageManager] Metadata loaded successfully');
      console.log(`[MedicalImageManager] Found ${this.metadata!.cases.length} cases`);
    } catch (error) {
      throw new Error(`Failed to load medical image metadata: ${(error as Error).message}`);
    }
  }

  /**
   * Get all available cases
   */
  getCases(): CaseMetadata[] {
    if (!this.metadata) {
      throw new Error('Metadata not loaded');
    }
    return this.metadata.cases;
  }

  /**
   * Get case by ID
   */
  getCase(caseId: string): CaseMetadata {
    if (!this.metadata) {
      throw new Error('Metadata not loaded');
    }

    const caseData = this.metadata.cases.find((c) => c.case_id === caseId);
    if (!caseData) {
      throw new Error(`Case ${caseId} not found`);
    }

    return caseData;
  }

  /**
   * Get all medical image files for a case
   */
  getCaseSlices(caseId: string): string[] {
    const caseData = this.getCase(caseId);

    return caseData.files.map((file) => {
      const filePath = path.join(this.baseDir, caseData.directory, file);

      if (!fs.existsSync(filePath)) {
        throw new Error(`Medical image file not found: ${filePath}`);
      }

      return filePath;
    });
  }

  /**
   * Get absolute paths for all medical image files
   */
  getCaseSlicesAbsolute(caseId: string): string[] {
    return this.getCaseSlices(caseId).map((file) => path.resolve(file));
  }

  /**
   * Get a specific slice by index
   */
  getSliceByIndex(caseId: string, index: number): string {
    const slices = this.getCaseSlices(caseId);

    if (index < 0 || index >= slices.length) {
      throw new Error(
        `Invalid slice index ${index} for case ${caseId}. ` +
        `Valid range: 0-${slices.length - 1}`
      );
    }

    return slices[index];
  }

  /**
   * Get the first slice (useful for quick tests)
   */
  getFirstSlice(caseId: string): string {
    return this.getSliceByIndex(caseId, 0);
  }

  /**
   * Get the middle slice
   */
  getMiddleSlice(caseId: string): string {
    const slices = this.getCaseSlices(caseId);
    const middleIndex = Math.floor(slices.length / 2);
    return slices[middleIndex];
  }

  /**
   * Get the last slice
   */
  getLastSlice(caseId: string): string {
    const slices = this.getCaseSlices(caseId);
    return slices[slices.length - 1];
  }

  /**
   * Get multiple random slices
   */
  getRandomSlices(caseId: string, count: number): string[] {
    const slices = this.getCaseSlices(caseId);

    if (count > slices.length) {
      throw new Error(
        `Cannot get ${count} random slices. Case ${caseId} only has ${slices.length} slices`
      );
    }

    // Shuffle and take first N
    const shuffled = [...slices].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, count);
  }

  /**
   * Get case metadata
   */
  getCaseMetadata(caseId: string): CaseMetadata {
    return this.getCase(caseId);
  }

  /**
   * Get slice count for a case
   */
  getSliceCount(caseId: string): number {
    const caseData = this.getCase(caseId);
    return caseData.file_count;
  }

  /**
   * Check if case has minimum number of slices
   */
  hasMinimumSlices(caseId: string, minCount: number): boolean {
    return this.getSliceCount(caseId) >= minCount;
  }

  /**
   * Validate that all medical image files exist
   */
  validateFiles(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!this.metadata) {
      return { valid: false, errors: ['Metadata not loaded'] };
    }

    this.metadata.cases.forEach((caseData) => {
      caseData.files.forEach((file) => {
        const filePath = path.join(this.baseDir, caseData.directory, file);

        if (!fs.existsSync(filePath)) {
          errors.push(`File not found: ${filePath}`);
        }
      });
    });

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Get total number of medical image files across all cases
   */
  getTotalFileCount(): number {
    if (!this.metadata) {
      return 0;
    }

    return this.metadata.cases.reduce((total, caseData) => {
      return total + caseData.file_count;
    }, 0);
  }

  /**
   * Print summary of available test data
   */
  printSummary(): void {
    if (!this.metadata) {
      console.log('[MedicalImageManager] No metadata loaded');
      return;
    }

    console.log('\n' + '='.repeat(50));
    console.log('Medical Image Test Data Summary');
    console.log('='.repeat(50));
    console.log(`Generated: ${this.metadata.generated_at}`);
    console.log(`Total Cases: ${this.metadata.cases.length}`);
    console.log(`Total Files: ${this.getTotalFileCount()}`);

    this.metadata.cases.forEach((caseData) => {
      console.log(`\nCase ${caseData.case_id}:`);
      console.log(`  Directory: ${caseData.directory}`);
      console.log(`  Slices: ${caseData.file_count}`);
      console.log(`  Modality: ${caseData.metadata.modality || 'Unknown'}`);
      console.log(`  Body Part: ${caseData.metadata.body_part || 'Unknown'}`);
      if (caseData.metadata.total_size_mb) {
        console.log(`  Size: ${caseData.metadata.total_size_mb} MB`);
      }
    });

    console.log('='.repeat(50) + '\n');
  }

  /**
   * Helper: Copy case files to a temporary directory
   */
  copyToTemp(caseId: string, tempDir: string): string[] {
    const slices = this.getCaseSlices(caseId);

    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }

    return slices.map((srcPath) => {
      const fileName = path.basename(srcPath);
      const destPath = path.join(tempDir, fileName);

      fs.copyFileSync(srcPath, destPath);
      return destPath;
    });
  }

  /**
   * Cleanup temporary files
   */
  cleanupTemp(tempDir: string): void {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  }
}

/**
 * Create medical image manager from default location
 */
export function createMedicalImageManager(): MedicalImageManager {
  const metadataPath = path.join(
    __dirname,
    '../fixtures/medical-data/metadata.json'
  );

  return new MedicalImageManager(metadataPath);
}
