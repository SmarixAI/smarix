import { NextResponse } from 'next/server';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';

// ---------- S3 CONFIGURATION ---------- //

const S3_BUCKET = process.env.AWS_BUCKET_NAME || 'smarix-data-apsouth1';
const S3_REGION = process.env.AWS_DEFAULT_REGION || 'ap-south-1';

const s3Client = new S3Client({
  region: S3_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

// ---------- API ROUTE ---------- //

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get('repo'); // e.g. "owner/repo"

    if (!repo) {
      return NextResponse.json(
        { error: 'Repository information (repo query param) is required' },
        { status: 400 }
      );
    }

    // Determine JSON filename
    const jsonFileName = 'onboarding_challenge_solution.json';

    // Construct S3 Key
    // Pattern: Onboarding/{owner}/{repo}/bugfix/{jsonFileName}
    const s3Key = `Onboarding/${repo}/bugfix/${jsonFileName}`;

    console.log(`Fetching Challenge Solutions from S3: ${s3Key}`);

    try {
      const command = new GetObjectCommand({
        Bucket: S3_BUCKET,
        Key: s3Key,
      });

      const s3Response = await s3Client.send(command);
      
      if (!s3Response.Body) {
        throw new Error('Empty body from S3');
      }

      const fileContent = await s3Response.Body.transformToString();
      const jsonData = JSON.parse(fileContent);

      return NextResponse.json(jsonData, {
        headers: {
          'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
        },
      });

    } catch (s3Error: any) {
      console.error("S3 Fetch Error:", s3Error);
      
      if (s3Error.name === 'NoSuchKey') {
        return NextResponse.json(
          { error: 'Challenge solution file not found in S3', key: s3Key },
          { status: 404 }
        );
      }
      
      throw s3Error;
    }

  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json({
      error: 'Failed to load challenge solution data',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}