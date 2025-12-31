import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET() {
  try {
    const possiblePaths = [
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data', 'onboarding_coding_questions.json'),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data', 'onboarding_coding_questions.json'),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data', 'onboarding_coding_questions.json'),
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
        { error: 'Coding questions file not found' },
        { status: 404 }
      );
    }

    const jsonData = JSON.parse(fileContent);

    return NextResponse.json(jsonData, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load coding questions',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const submissionData = await request.json();

    const possibleBasePaths = [
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data'),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data'),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data'),
      path.join(process.cwd(), 'backend/data/Onboarding/onboarding_bugfix_data'),
    ];

    let basePath: string | null = null;

    for (const testPath of possibleBasePaths) {
      try {
        await fs.access(testPath);
        basePath = testPath;
        break;
      } catch {
        continue;
      }
    }

    if (!basePath) {
      for (const testPath of possibleBasePaths) {
        try {
          await fs.mkdir(testPath, { recursive: true });
          basePath = testPath;
          break;
        } catch {
          continue;
        }
      }
    }

    if (!basePath) {
      return NextResponse.json(
        { 
          success: false,
          error: 'Could not find or create directory for submissions' 
        },
        { status: 500 }
      );
    }

    const filePath = path.join(basePath, 'onboarding_challenge_submitted_code.json');

    let existingData: any = {
      metadata: {
        total_submissions: 0,
        last_updated: new Date().toISOString()
      },
      submissions: []
    };

    try {
      await fs.access(filePath);
      const fileContent = await fs.readFile(filePath, 'utf-8');
      existingData = JSON.parse(fileContent);
    } catch {
      console.log('Creating new submissions file');
    }

    const newSubmission = {
      submission_id: `sub_${Date.now()}`,
      pr_number: submissionData.pr_number,
      submitted_at: submissionData.timestamp,
      file_changes: submissionData.file_changes
    };

    existingData.submissions.push(newSubmission);
    existingData.metadata.total_submissions = existingData.submissions.length;
    existingData.metadata.last_updated = new Date().toISOString();

    await fs.writeFile(filePath, JSON.stringify(existingData, null, 2), 'utf-8');

    return NextResponse.json({
      success: true,
      message: 'Code submitted successfully',
      submission_id: newSubmission.submission_id
    });

  } catch (error) {
    console.error('Error saving submission:', error);
    return NextResponse.json(
      { 
        success: false, 
        message: 'Failed to submit code',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
