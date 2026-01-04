import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { PRACTICE_MODULE_FILE_MAPPING } from '../../../../../components/onboarding/constants/Practice/modules';

// ---------- TYPES ---------- //

interface PracticeStep {
  step_number: number;
  step_title: string;
  what_to_do: string;
  code_snippet: string;
  code_line_count?: number;
  tips?: string[];
  common_mistakes?: string[];
}

interface PracticeTask {
  question_number: number;
  difficulty: string;
  type: string;
  raw_response?: string;
  question_description?: string;
  steps: PracticeStep[];
}

interface PracticeJSONData {
  metadata?: Record<string, any>;
  questions?: PracticeTask[];
  [key: string]: any;
}

// ---------- API ROUTE ---------- //

export async function GET(
  request: Request,
  { params }: { params: Promise<{ moduleId: string }> }
) {
  try {
    const { moduleId } = await params;
    const jsonFileName = PRACTICE_MODULE_FILE_MAPPING[moduleId];

    if (!jsonFileName) {
      return NextResponse.json(
        { error: 'Practice module not found', moduleId },
        { status: 404 }
      );
    }

    const { searchParams } = new URL(request.url);
    const repo = searchParams.get('repo');

    // Helper function to find file in repo folders
    const findFileInRepos = async (basePaths: string[], fileName: string, repo?: string | null): Promise<string | null> => {
      for (const basePath of basePaths) {
        try {
          // If repo is provided, try owner/repo structure first
          if (repo) {
            const [owner, repoName] = repo.split('/');
            // Try new structure: owner/repo/onboarding_practice_data/
            const newPath = path.join(basePath, owner, repoName, 'onboarding_practice_data', fileName);
            try {
              await fs.access(newPath);
              return newPath;
            } catch {
              // Try alternative: owner/repo/practice/
              const altPath = path.join(basePath, owner, repoName, 'practice', fileName);
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
              try {
                const ownerEntries = await fs.readdir(ownerPath, { withFileTypes: true });
                for (const repoEntry of ownerEntries) {
                  if (repoEntry.isDirectory()) {
                    // Try new structure: owner/repo/onboarding_practice_data/
                    const newPath = path.join(ownerPath, repoEntry.name, 'onboarding_practice_data', fileName);
                    try {
                      await fs.access(newPath);
                      return newPath;
                    } catch {
                      // Try alternative: owner/repo/practice/
                      const altPath = path.join(ownerPath, repoEntry.name, 'practice', fileName);
                      try {
                        await fs.access(altPath);
                        return altPath;
                      } catch {
                        continue;
                      }
                    }
                  }
                }
              } catch {
                // Not owner/repo structure, try flat
              }
              
              // Try flat repo structure: repo_name/onboarding_practice_data/
              const flatPath = path.join(ownerPath, entry.name, 'onboarding_practice_data', fileName);
              try {
                await fs.access(flatPath);
                return flatPath;
              } catch {
                continue;
              }
            }
          }
          
          // Try old structure (direct file)
          const oldPath = path.join(basePath, 'onboarding_practice_data', fileName);
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
        { error: 'Practice module file not found', fileName: jsonFileName },
        { status: 404 }
      );
    }

    const fileContent = await fs.readFile(filePath, 'utf-8');

    const jsonData: PracticeJSONData = JSON.parse(fileContent);

    return NextResponse.json(
      {
        moduleId,
        jsonFile: jsonFileName,
        metadata: jsonData.metadata,
        tasks: jsonData.questions || [],
        totalTasks: jsonData.questions?.length || 0,
      },
      {
        headers: {
          "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
        },
      }
    );

  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to load Practice module",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
