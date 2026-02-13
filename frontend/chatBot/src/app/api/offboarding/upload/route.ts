import { NextRequest, NextResponse } from 'next/server';
import { uploadFileToS3, readFileFromS3 } from '../../../../components/offboarding/s3Utils';

const UPLOAD_SUBFOLDER = 'upload';

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
    const fileName = `${taskId}.txt`;
    const buffer = await readFileFromS3(employeeId, UPLOAD_SUBFOLDER, fileName);
    return new NextResponse(buffer, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Disposition': `attachment; filename="${fileName}"`,
      },
    });
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    const code = (error as { Code?: string; name?: string })?.Code ?? (error as { Code?: string; name?: string })?.name;
    const isNotFound = code === 'NoSuchKey' || msg.includes('NoSuchKey') || msg.includes('Empty response');
    if (isNotFound) {
      return NextResponse.json({ error: 'Uploaded file not found' }, { status: 404 });
    }
    console.error('Offboarding upload GET error:', error);
    return NextResponse.json(
      { error: 'Failed to download file', details: msg },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const employeeId = formData.get('employeeId')?.toString()?.trim();
    const taskId = formData.get('taskId')?.toString()?.trim();
    const file = formData.get('file') as File | null;

    if (!employeeId || !taskId) {
      return NextResponse.json(
        { error: 'employeeId and taskId are required' },
        { status: 400 }
      );
    }
    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { error: 'file is required' },
        { status: 400 }
      );
    }
    if (!file.name.toLowerCase().endsWith('.txt')) {
      return NextResponse.json(
        { error: 'Only .txt files are allowed' },
        { status: 400 }
      );
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    const fileName = `${taskId}.txt`;
    await uploadFileToS3(employeeId, UPLOAD_SUBFOLDER, fileName, buffer, 'text/plain');

    return NextResponse.json({
      success: true,
      key: `Offboarding/${employeeId}/${UPLOAD_SUBFOLDER}/${fileName}`,
    });
  } catch (error) {
    console.error('Offboarding upload error:', error);
    return NextResponse.json(
      {
        error: 'Failed to upload file',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
