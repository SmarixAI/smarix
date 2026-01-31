import { NextResponse } from "next/server";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { PRACTICE_MODULE_FILE_MAPPING } from "../../../../../components/onboarding/constants/Practice/modules";

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

// ---------- S3 CONFIGURATION ---------- //

const S3_BUCKET = process.env.AWS_BUCKET_NAME || "smarix-data-apsouth1";
const S3_REGION = process.env.AWS_DEFAULT_REGION || "ap-south-1";

const s3Client = new S3Client({
  region: S3_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

// ---------- API ROUTE ---------- //

export async function GET(
  request: Request,
  { params }: { params: Promise<{ moduleId: string }> },
) {
  try {
    const { moduleId } = await params;
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get("repo"); // e.g. "owner/repo"

    if (!repo) {
      return NextResponse.json(
        { error: "Repository information (repo query param) is required" },
        { status: 400 },
      );
    }

    const jsonFileName = PRACTICE_MODULE_FILE_MAPPING[moduleId];

    if (!jsonFileName) {
      return NextResponse.json(
        { error: "Practice module not found", moduleId },
        { status: 404 },
      );
    }

    // Construct S3 Key
    // Pattern: Onboarding/{owner}/{repo}/practice/{jsonFileName}
    const s3Key = `Onboarding/${repo}/practice/${jsonFileName}`;

    console.log(`Fetching Practice Module from S3: ${s3Key}`);

    try {
      const command = new GetObjectCommand({
        Bucket: S3_BUCKET,
        Key: s3Key,
      });

      const s3Response = await s3Client.send(command);

      if (!s3Response.Body) {
        throw new Error("Empty body from S3");
      }

      const fileContent = await s3Response.Body.transformToString();
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
            "Cache-Control":
              "public, s-maxage=3600, stale-while-revalidate=86400",
          },
        },
      );
    } catch (s3Error: any) {
      console.error("S3 Fetch Error:", s3Error);

      if (s3Error.name === "NoSuchKey") {
        return NextResponse.json(
          { error: "Practice module file not found in S3", key: s3Key },
          { status: 404 },
        );
      }

      throw s3Error;
    }
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      {
        error: "Failed to load Practice module",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}
