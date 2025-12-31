import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET() {
  try {
    const possiblePaths = [
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data', 'onboarding_pr_tutorials.json'),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data', 'onboarding_pr_tutorials.json'),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding', 'onboarding_bugfix_data', 'onboarding_pr_tutorials.json'),
      path.join(process.cwd(), 'backend/data/Onboarding/onboarding_bugfix_data', 'onboarding_pr_tutorials.json'),
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
        { error: 'PR tutorials file not found' },
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
      error: 'Failed to load PR tutorials',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}
