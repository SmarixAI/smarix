import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { QA_MODULE_FILE_MAPPING } from '../../../../../components/onboarding/constants/QASession/modules';

interface QuestionData {
  question_number: number;
  question: string;
  options: Record<string, string>;
  correct_answer: string;
  explanation: string;
}

interface JSONData {
  metadata?: {
    focus?: string;
    generated_at?: string;
    repository?: string;
  };
  questions?: QuestionData[];
  [key: string]: any;
}

// Mapping from new module IDs (from employee_onboarding_tasks.json) to file names
const NEW_ID_TO_FILE_MAPPING: { [key: string]: string } = {
  'overview': 'onboarding_overview_questions.json',
  'tech_stack': 'onboarding_tech_stack_questions.json',
  'repo_structure': 'onboarding_repo_structure_questions.json',
  'app_features': 'onboarding_app_features_questions.json',
  'dev_setup': 'onboarding_dev_setup_questions.json',
  'code_conventions': 'onboarding_code_conventions_questions.json',
};

export async function GET(
  request: Request,
  { params }: { params: Promise<{ moduleId: string }> }
) {
  try {
    const { moduleId } = await params;
    // Try new ID format first, then fall back to old format
    const jsonFileName = NEW_ID_TO_FILE_MAPPING[moduleId] || QA_MODULE_FILE_MAPPING[moduleId];

    if (!jsonFileName) {
      return NextResponse.json(
        { error: 'Q&A module not found', moduleId },
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
            // Try new structure: owner/repo/onboarding_QnA_data/
            const newPath = path.join(basePath, owner, repoName, 'onboarding_QnA_data', fileName);
            try {
              await fs.access(newPath);
              return newPath;
            } catch {
              // Try alternative: owner/repo/qna/
              const altPath = path.join(basePath, owner, repoName, 'qna', fileName);
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
                    // Try new structure: owner/repo/onboarding_QnA_data/
                    const newPath = path.join(ownerPath, repoEntry.name, 'onboarding_QnA_data', fileName);
                    try {
                      await fs.access(newPath);
                      return newPath;
                    } catch {
                      // Try alternative: owner/repo/qna/
                      const altPath = path.join(ownerPath, repoEntry.name, 'qna', fileName);
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
              
              // Try flat repo structure: repo_name/onboarding_QnA_data/
              const flatPath = path.join(ownerPath, entry.name, 'onboarding_QnA_data', fileName);
              try {
                await fs.access(flatPath);
                return flatPath;
              } catch {
                continue;
              }
            }
          }
          
          // Try old structure (direct file)
          const oldPath = path.join(basePath, 'onboarding_QnA_data', fileName);
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
        { error: 'Q&A module file not found' },
        { status: 404 }
      );
    }

    const fileContent = await fs.readFile(filePath, 'utf-8');

    const jsonData: JSONData = JSON.parse(fileContent);

    return NextResponse.json({
      moduleId,
      jsonFile: jsonFileName,
      metadata: jsonData.metadata,
      questions: jsonData.questions || [],
      totalQuestions: jsonData.questions?.length || 0,
    }, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load Q&A module',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}
