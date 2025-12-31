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

    const possiblePaths = [
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding', 'onboarding_QnA_data', jsonFileName),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding', 'onboarding_QnA_data', jsonFileName),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding', 'onboarding_QnA_data', jsonFileName),
      path.join(process.cwd(), 'backend/data/Onboarding/onboarding_QnA_data', jsonFileName),
    ];

    let fileContent: string | null = null;

    for (const filePath of possiblePaths) {
      try {
        await fs.access(filePath);
        fileContent = await fs.readFile(filePath, 'utf-8');
        break;
      } catch {
        continue;
      }
    }

    if (!fileContent) {
      return NextResponse.json(
        { error: 'Q&A module file not found' },
        { status: 404 }
      );
    }

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
