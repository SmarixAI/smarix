import { NextRequest, NextResponse } from "next/server";
import {
  S3Client,
  GetObjectCommand,
  PutObjectCommand,
} from "@aws-sdk/client-s3";

const S3_BUCKET = process.env.AWS_BUCKET_NAME || "smarix-data-apsouth1";
const S3_REGION = process.env.AWS_DEFAULT_REGION || "ap-south-1";

const s3Client = new S3Client({
  region: S3_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

// GET: List all challenges
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get("repo");

    if (!repo)
      return NextResponse.json({ error: "Repo required" }, { status: 400 });

    const s3Key = `Onboarding/${repo}/bugfix/onboarding_coding_questions.json`;

    try {
      const command = new GetObjectCommand({ Bucket: S3_BUCKET, Key: s3Key });
      const s3Response = await s3Client.send(command);

      if (!s3Response.Body) throw new Error("Empty body");

      const fileContent = await s3Response.Body.transformToString();
      return NextResponse.json(JSON.parse(fileContent), {
        headers: { "Cache-Control": "public, s-maxage=3600" },
      });
    } catch (s3Error: any) {
      if (s3Error.name === "NoSuchKey") {
        return NextResponse.json(
          { error: "Not found", key: s3Key },
          { status: 404 },
        );
      }
      throw s3Error;
    }
  } catch (error) {
    return NextResponse.json({ error: "Internal Error" }, { status: 500 });
  }
}

// POST: Submit Solution
export async function POST(request: NextRequest) {
  try {
    const submissionData = await request.json();
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get("repo");

    if (!repo)
      return NextResponse.json({ error: "Repo required" }, { status: 400 });

    const s3Key = `Onboarding/${repo}/bugfix/onboarding_challenge_submitted_code.json`;

    let existingData: any = {
      metadata: {
        total_submissions: 0,
        last_updated: new Date().toISOString(),
      },
      submissions: [],
    };

    try {
      const getCommand = new GetObjectCommand({
        Bucket: S3_BUCKET,
        Key: s3Key,
      });
      const s3Response = await s3Client.send(getCommand);
      if (s3Response.Body) {
        existingData = JSON.parse(await s3Response.Body.transformToString());
      }
    } catch (e: any) {
      /* Ignore if new file */
    }

    // ✅ FIX 1: Generate ID separately so we can return it
    const submissionId = `sub_${Date.now()}`;

    const newSubmission = {
      submission_id: submissionId, // Use the generated ID
      pr_number: submissionData.pr_number,
      submitted_at: submissionData.timestamp || new Date().toISOString(),
      file_changes: submissionData.file_changes,
    };

    if (!existingData.submissions) existingData.submissions = [];
    existingData.submissions.push(newSubmission);
    existingData.metadata.last_updated = new Date().toISOString();
    existingData.metadata.total_submissions = existingData.submissions.length;

    await s3Client.send(
      new PutObjectCommand({
        Bucket: S3_BUCKET,
        Key: s3Key,
        Body: JSON.stringify(existingData, null, 2),
        ContentType: "application/json",
      }),
    );

    return NextResponse.json({
      success: true,
      submission_id: submissionId,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 },
    );
  }
}
