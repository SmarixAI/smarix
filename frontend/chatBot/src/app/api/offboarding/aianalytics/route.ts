import { NextRequest, NextResponse } from 'next/server';
import { readJsonFromS3, writeJsonToS3 } from '../../../../components/offboarding/s3Utils';

function getAIReportFileName(taskId: string): string {
  return `aianalytics/${taskId}.json`;
}

export async function GET(request: NextRequest) {
  const employeeId = request.nextUrl.searchParams.get('employeeId')?.trim();
  const taskId = request.nextUrl.searchParams.get('taskId')?.trim();

  if (!employeeId || !taskId) {
    return NextResponse.json(
      { error: 'employeeId and taskId query params are required' },
      { status: 400 }
    );
  }

  try {
    const report = await readJsonFromS3(getAIReportFileName(taskId), employeeId);
    return NextResponse.json(report);
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    if (msg.includes('NoSuchKey') || msg.includes('None of the files found')) {
      return NextResponse.json({ error: 'Report not found' }, { status: 404 });
    }
    console.error('Offboarding AI analytics GET error:', error);
    return NextResponse.json(
      { error: 'Failed to load report', details: msg },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { employeeId, taskId, report } = body;

    if (!employeeId?.trim() || !taskId?.trim()) {
      return NextResponse.json(
        { error: 'employeeId and taskId are required' },
        { status: 400 }
      );
    }
    if (report === undefined) {
      return NextResponse.json(
        { error: 'report object is required' },
        { status: 400 }
      );
    }

    const fileName = getAIReportFileName(taskId);
    await writeJsonToS3(fileName, report, employeeId);

    return NextResponse.json({
      success: true,
      key: `Offboarding/${employeeId}/${fileName}`,
    });
  } catch (error) {
    console.error('Offboarding AI analytics POST error:', error);
    return NextResponse.json(
      {
        error: 'Failed to save report',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
