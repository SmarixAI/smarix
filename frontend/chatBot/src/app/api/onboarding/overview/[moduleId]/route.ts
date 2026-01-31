import { NextResponse } from 'next/server';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { MODULE_FILE_MAPPING, getModuleName } from '../../../../../components/onboarding/constants/ReadingOverview/modules';

// --- S3 Configuration ---
const S3_BUCKET = process.env.AWS_BUCKET_NAME || 'smarix-data-apsouth1';
const S3_REGION = process.env.AWS_DEFAULT_REGION || 'ap-south-1';

const s3Client = new S3Client({
  region: S3_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

interface JSONData {
  metadata?: any;
  data?: Record<string, any>;
  sections?: Record<string, any>;
  [key: string]: any;
}

function extractGroupedSections(jsonData: JSONData) {
  // Robust check: try root .sections, or .data.sections
  const sectionsData = jsonData.sections || (jsonData.data && jsonData.data.sections);

  if (!sectionsData || typeof sectionsData !== 'object') {
    console.warn("⚠️ extractGroupedSections: No 'sections' found in JSON");
    return [];
  }

  return Object.entries(sectionsData).map(([sectionKey, sectionValue]) => {
    // @ts-ignore
    const val = sectionValue as any;
    const teaching = val.teaching_content ?? [];
    const qna = val.qna ?? [];

    const items = [
      ...teaching.map((t: any) => ({ type: 'teaching_content', ...t })),
      ...(qna.length > 0 ? [{
        type: 'qna',
        questions: qna,
        sectionKey
      }] : [])
    ];

    return {
      sectionId: sectionKey,
      sectionTitle: sectionKey
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase()),
      items
    };
  });
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ moduleId: string }> }
) {
  try {
    const { moduleId } = await params;
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get('repo');
    
    if (!repo) {
      return NextResponse.json({ error: 'Repo param required' }, { status: 400 });
    }

    const normalizedModuleId = getModuleName(moduleId);
    const jsonFileName = MODULE_FILE_MAPPING[normalizedModuleId] || MODULE_FILE_MAPPING[moduleId];

    if (!jsonFileName) {
      return NextResponse.json({ error: 'Module not found' }, { status: 404 });
    }

    const s3Key = `Onboarding/${repo}/reading/${jsonFileName}`;
    console.log(`Fetching from S3: ${s3Key}`);

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
      const jsonData: JSONData = JSON.parse(fileContent);
      
      // Log keys to debug structure issues
      // console.log("Fetched JSON Keys:", Object.keys(jsonData));

      const sections = extractGroupedSections(jsonData);

      return NextResponse.json({
        moduleId,
        jsonFile: jsonFileName,
        sections,
        totalSections: sections.length,
      }, {
        headers: {
          'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
        },
      });

    } catch (s3Error: any) {
      console.error("S3 Fetch Error:", s3Error);
      if (s3Error.name === 'NoSuchKey') {
        return NextResponse.json({ error: 'File not found in S3', key: s3Key }, { status: 404 });
      }
      throw s3Error;
    }

  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json({
      error: 'Failed to load module',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}