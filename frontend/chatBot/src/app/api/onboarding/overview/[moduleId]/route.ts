import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { MODULE_FILE_MAPPING } from '../../../../../components/onboarding/constants/ReadingOverview/modules';

interface JSONData {
  metadata?: any;
  data?: Record<string, any>;
  sections?: Record<string, any>;
  [key: string]: any;
}

function extractSections(jsonData: JSONData): Record<string, any> {
  if (jsonData.data && typeof jsonData.data === 'object') {
    return jsonData.data;
  }
  
  if (jsonData.sections && typeof jsonData.sections === 'object') {
    const firstValue = Object.values(jsonData.sections)[0];
    
    if (firstValue && typeof firstValue === 'object' && ('question' in firstValue || 'answer' in firstValue)) {
      return jsonData.sections;
    } else {
      const allData: Record<string, any> = {};
      for (const category of Object.values(jsonData.sections)) {
        if (typeof category === 'object' && !Array.isArray(category)) {
          Object.assign(allData, category);
        }
      }
      return allData;
    }
  }
  
  for (const [key, value] of Object.entries(jsonData)) {
    if (key !== 'metadata' && value && typeof value === 'object' && !Array.isArray(value)) {
      return value;
    }
  }
  
  return {};
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ moduleId: string }> }
) {
  try {
    const { moduleId } = await params;
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get('repo');
    
    const jsonFileName = MODULE_FILE_MAPPING[moduleId];

    if (!jsonFileName) {
      return NextResponse.json(
        { error: 'Module not found' },
        { status: 404 }
      );
    }

    let possiblePaths: string[];

    // Helper function to find file in repo folders or old structure
    const findFileInRepos = async (basePaths: string[], fileName: string, repo?: string): Promise<string | null> => {
      for (const basePath of basePaths) {
        try {
          // If repo is provided, try owner/repo structure first
          if (repo) {
            const [owner, repoName] = repo.split('/');
            // Try new structure: owner/repo/onboarding_reading_data/
            const newPath = path.join(basePath, owner, repoName, 'onboarding_reading_data', fileName);
            try {
              await fs.access(newPath);
              return newPath;
            } catch {
              // Try alternative: owner/repo/reading/
              const altPath = path.join(basePath, owner, repoName, 'reading', fileName);
              try {
                await fs.access(altPath);
                return altPath;
              } catch {
                // Continue to scan
              }
            }
          }
          
          // Scan repo folders for the file
          const entries = await fs.readdir(basePath, { withFileTypes: true });
          for (const entry of entries) {
            if (entry.isDirectory()) {
              // Check if it's owner/repo structure
              const ownerPath = path.join(basePath, entry.name);
              const ownerEntries = await fs.readdir(ownerPath, { withFileTypes: true });
              for (const repoEntry of ownerEntries) {
                if (repoEntry.isDirectory()) {
                  // Try new structure: owner/repo/onboarding_reading_data/
                  const newPath = path.join(ownerPath, repoEntry.name, 'onboarding_reading_data', fileName);
                  try {
                    await fs.access(newPath);
                    return newPath;
                  } catch {
                    // Try alternative: owner/repo/reading/
                    const altPath = path.join(ownerPath, repoEntry.name, 'reading', fileName);
                    try {
                      await fs.access(altPath);
                      return altPath;
                    } catch {
                      continue;
                    }
                  }
                }
              }
              
              // Try flat repo structure: repo_name/onboarding_reading_data/
              const flatPath = path.join(ownerPath, entry.name, 'onboarding_reading_data', fileName);
              try {
                await fs.access(flatPath);
                return flatPath;
              } catch {
                continue;
              }
            }
          }
          
          // Try old structure (direct file)
          const oldPath = path.join(basePath, 'onboarding_reading_data', fileName);
          try {
            await fs.access(oldPath);
            return oldPath;
          } catch {
            continue;
          }
        } catch {
          continue;
        }
      }
      return null;
    };

    const possibleBasePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding'),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding'),
    ];

    const filePath = await findFileInRepos(possibleBasePaths, jsonFileName, repo);
    
    if (!filePath) {
      return NextResponse.json(
        { error: 'Module file not found' },
        { status: 404 }
      );
    }

    const fileContent = await fs.readFile(filePath, 'utf-8');

    const jsonData: JSONData = JSON.parse(fileContent);
    const moduleData = extractSections(jsonData);

    const sections = Object.keys(moduleData).map((key, index) => ({
      sectionId: `${moduleId}-${index + 1}`,
      sectionTitle: key,
      content: moduleData[key],
    }));

    return NextResponse.json({
      moduleId,
      jsonFile: jsonFileName,
      sections,
      totalSections: sections.length,
    }, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load module',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}
