import { NextResponse } from "next/server";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";

const S3_BUCKET = process.env.AWS_BUCKET_NAME || "smarix-data-apsouth1";
const S3_REGION = process.env.AWS_DEFAULT_REGION || "ap-south-1";

const s3Client = new S3Client({
  region: S3_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get("repo");

    if (!repo)
      return NextResponse.json({ error: "Repo required" }, { status: 400 });

    // ✅ Ensure this matches your S3 filename exactly
    const s3Key = `Onboarding/${repo}/bugfix/onboarding_challenge_solution.json`;

    const command = new GetObjectCommand({ Bucket: S3_BUCKET, Key: s3Key });
    const s3Response = await s3Client.send(command);

    const fileContent = await s3Response.Body?.transformToString();
    if (!fileContent) throw new Error("Empty body");

    const jsonData = JSON.parse(fileContent);
    return NextResponse.json(jsonData);
  } catch (error: any) {
    console.error("Solutions API Error:", error);
    // Return empty array instead of error to prevent UI crash
    if (error.name === "NoSuchKey")
      return NextResponse.json({ pull_requests: [] });
    return NextResponse.json(
      { error: "Failed to load solutions" },
      { status: 500 },
    );
  }
}
