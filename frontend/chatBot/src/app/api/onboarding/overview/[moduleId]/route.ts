import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { MODULE_FILE_MAPPING } from '../../../../../components/onboarding/constants/ReadingOverview/modules';

interface JSONData {
  metadata?: any;
  data?: Record<string, any>;
  sections?: Record<string, any>;
  [key: string]: any;
}

function extractSections(jsonData: JSONData): Record<string, any> {
  if (jsonData.data && typeof jsonData.data === 'object') {
    return jsonData.data;
  }
  
  if (jsonData.sections && typeof jsonData.sections === 'object') {
    const firstValue = Object.values(jsonData.sections)[0];
    
    if (firstValue && typeof firstValue === 'object' && ('question' in firstValue || 'answer' in firstValue)) {
      return jsonData.sections;
    } else {
      const allData: Record<string, any> = {};
      for (const category of Object.values(jsonData.sections)) {
        if (typeof category === 'object' && !Array.isArray(category)) {
          Object.assign(allData, category);
        }
      }
      return allData;
    }
  }
  
  for (const [key, value] of Object.entries(jsonData)) {
    if (key !== 'metadata' && value && typeof value === 'object' && !Array.isArray(value)) {
      return value;
    }
  }
  
  return {};
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ moduleId: string }> }
) {
  try {
    const { moduleId } = await params;
    const jsonFileName = MODULE_FILE_MAPPING[moduleId];

    if (!jsonFileName) {
      return NextResponse.json(
        { error: 'Module not found' },
        { status: 404 }
      );
    }

    const possiblePaths = [
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding', 'onboarding_reading_data', jsonFileName),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding', 'onboarding_reading_data', jsonFileName),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding', 'onboarding_reading_data', jsonFileName),
      path.join(process.cwd(), 'backend/data/Onboarding/onboarding_reading_data', jsonFileName),
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
        { error: 'Module file not found' },
        { status: 404 }
      );
    }

    const jsonData: JSONData = JSON.parse(fileContent);
    const moduleData = extractSections(jsonData);

    const sections = Object.keys(moduleData).map((key, index) => ({
      sectionId: `${moduleId}-${index + 1}`,
      sectionTitle: key,
      content: moduleData[key],
    }));

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
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load module',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}
