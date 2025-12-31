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

    // Paths to try (same approach as your Q&A code)
    const possiblePaths = [
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding', 'onboarding_practice_data', jsonFileName),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding', 'onboarding_practice_data', jsonFileName),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding', 'onboarding_practice_data', jsonFileName),
      path.join(process.cwd(), 'backend/data/Onboarding/onboarding_practice_data', jsonFileName),
    ];

    let fileContent: string | null = null;

    for (const p of possiblePaths) {
      try {
        await fs.access(p);
        fileContent = await fs.readFile(p, 'utf-8');
        break;
      } catch {
        // Try next path silently
        continue;
      }
    }

    if (!fileContent) {
      return NextResponse.json(
        { error: 'Practice module file not found', fileName: jsonFileName },
        { status: 404 }
      );
    }

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
