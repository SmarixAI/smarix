import { NextResponse } from 'next/server';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';

const S3_BUCKET = process.env.AWS_BUCKET_NAME || 'smarix-data-apsouth1';
const S3_REGION = process.env.AWS_DEFAULT_REGION || 'ap-south-1';

const s3Client = new S3Client({
  region: S3_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get('repo');
    const { id } = await params;

    if (!repo) {
      return NextResponse.json({ error: 'Repo param required' }, { status: 400 });
    }

    const s3Key = `Onboarding/${repo}/bugfix/onboarding_coding_questions.json`;

    try {
      const command = new GetObjectCommand({ Bucket: S3_BUCKET, Key: s3Key });
      const s3Response = await s3Client.send(command);
      
      if (!s3Response.Body) throw new Error('Empty body');
      
      const fileContent = await s3Response.Body.transformToString();
      const jsonData = JSON.parse(fileContent);

      // Support "questions" or "tasks" array structure
      const questions = jsonData.questions || jsonData.tasks || [];
      
      // FIND THE SPECIFIC CHALLENGE
      const challenge = questions.find(
        (q: any) => q.question_number?.toString() === id.toString()
      );

      if (!challenge) {
        return NextResponse.json({ error: 'Challenge not found', id }, { status: 404 });
      }

      return NextResponse.json(challenge, {
        headers: { 'Cache-Control': 'public, s-maxage=3600' }
      });

    } catch (s3Error: any) {
      if (s3Error.name === 'NoSuchKey') {
        return NextResponse.json({ error: 'File not found', key: s3Key }, { status: 404 });
      }
      throw s3Error;
    }
  } catch (error) {
    console.error("Single Challenge API Error:", error);
    return NextResponse.json({ error: 'Internal Error' }, { status: 500 });
  }
}