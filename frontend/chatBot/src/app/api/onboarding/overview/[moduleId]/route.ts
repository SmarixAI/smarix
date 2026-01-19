import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { MODULE_FILE_MAPPING, getModuleName } from '../../../../../components/onboarding/constants/ReadingOverview/modules';

interface JSONData {
  metadata?: any;
  data?: Record<string, any>;
  sections?: Record<string, any>;
  [key: string]: any;
}

function groupTeachingThenQna(teachingContent: any[], qna: any[], prefix: string = ''): Record<string, any> {
  const grouped: Record<string, any> = {};
  let index = 1;
  
  // Add all teaching_content items first (each as separate page)
  teachingContent.forEach((item) => {
    const key = prefix ? `${prefix}_teaching_content_${index}` : `teaching_content_${index}`;
    grouped[key] = {
      type: 'teaching_content',
      ...item
    };
    index++;
  });
  
  // Then add all qna items together as a single page
  if (qna.length > 0) {
    const key = prefix ? `${prefix}_qna_all` : `qna_all`;
    grouped[key] = {
      type: 'qna',
      questions: qna, // All questions in an array
      sectionKey: prefix
    };
  }
  
  return grouped;
}

function extractSections(jsonData: JSONData): Record<string, any> {
  if (jsonData.data && typeof jsonData.data === 'object') {
    // Check if data has teaching_content and qna arrays
    const teachingContent = jsonData.data.teaching_content;
    const qna = jsonData.data.qna;
    
    if (Array.isArray(teachingContent) && Array.isArray(qna)) {
      return groupTeachingThenQna(teachingContent, qna);
    }
    
    return jsonData.data;
  }
  
  if (jsonData.sections && typeof jsonData.sections === 'object') {
    const firstValue = Object.values(jsonData.sections)[0];
    
    // Check if it's a QnA-only structure (old format)
    if (firstValue && typeof firstValue === 'object' && ('question' in firstValue || 'answer' in firstValue)) {
      return jsonData.sections;
    }
    
    // Process sections structure - handle both sections.data and sections.{section_name}
    const interleavedSections: Record<string, any> = {};
    
    for (const [sectionKey, sectionValue] of Object.entries(jsonData.sections)) {
      if (typeof sectionValue === 'object' && !Array.isArray(sectionValue)) {
        const teachingContent = sectionValue.teaching_content;
        const qna = sectionValue.qna;
        
        if (Array.isArray(teachingContent) && Array.isArray(qna)) {
          // Group all teaching_content first, then all qna for this section
          const grouped = groupTeachingThenQna(teachingContent, qna, sectionKey);
          Object.assign(interleavedSections, grouped);
        } else {
          // If no interleaving needed, keep original structure
          interleavedSections[sectionKey] = sectionValue;
        }
      }
    }
    
    return interleavedSections;
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
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get('repo');
    
    // Normalize moduleId to string name if it's numeric
    const normalizedModuleId = getModuleName(moduleId);
    const jsonFileName = MODULE_FILE_MAPPING[normalizedModuleId] || MODULE_FILE_MAPPING[moduleId];

    if (!jsonFileName) {
      return NextResponse.json(
        { error: 'Module not found' },
        { status: 404 }
      );
    }

    let possiblePaths: string[];

    // Helper function to find file in repo folders or old structure
    const findFileInRepos = async (basePaths: string[], fileName: string, repo?: string): Promise<string | null> => {
      for (const basePath of basePaths) {
        try {
          // If repo is provided, try owner/repo structure first
          if (repo) {
            const [owner, repoName] = repo.split('/');
            // Try new structure: owner/repo/onboarding_reading_data/
            const newPath = path.join(basePath, owner, repoName, 'onboarding_reading_data', fileName);
            try {
              await fs.access(newPath);
              return newPath;
            } catch {
              // Try alternative: owner/repo/reading/
              const altPath = path.join(basePath, owner, repoName, 'reading', fileName);
              try {
                await fs.access(altPath);
                return altPath;
              } catch {
                // Continue to scan
              }
            }
          }
          
          // Scan repo folders for the file
          const entries = await fs.readdir(basePath, { withFileTypes: true });
          for (const entry of entries) {
            if (entry.isDirectory()) {
              // Check if it's owner/repo structure
              const ownerPath = path.join(basePath, entry.name);
              const ownerEntries = await fs.readdir(ownerPath, { withFileTypes: true });
              for (const repoEntry of ownerEntries) {
                if (repoEntry.isDirectory()) {
                  // Try new structure: owner/repo/onboarding_reading_data/
                  const newPath = path.join(ownerPath, repoEntry.name, 'onboarding_reading_data', fileName);
                  try {
                    await fs.access(newPath);
                    return newPath;
                  } catch {
                    // Try alternative: owner/repo/reading/
                    const altPath = path.join(ownerPath, repoEntry.name, 'reading', fileName);
                    try {
                      await fs.access(altPath);
                      return altPath;
                    } catch {
                      continue;
                    }
                  }
                }
              }
              
              // Try flat repo structure: repo_name/onboarding_reading_data/
              const flatPath = path.join(ownerPath, entry.name, 'onboarding_reading_data', fileName);
              try {
                await fs.access(flatPath);
                return flatPath;
              } catch {
                continue;
              }
            }
          }
          
          // Try old structure (direct file)
          const oldPath = path.join(basePath, 'onboarding_reading_data', fileName);
          try {
            await fs.access(oldPath);
            return oldPath;
          } catch {
            continue;
          }
        } catch {
          continue;
        }
      }
      return null;
    };

    const possibleBasePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding'),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding'),
    ];

    const filePath = await findFileInRepos(possibleBasePaths, jsonFileName, repo);
    
    if (!filePath) {
      return NextResponse.json(
        { error: 'Module file not found' },
        { status: 404 }
      );
    }

    const fileContent = await fs.readFile(filePath, 'utf-8');

    const jsonData: JSONData = JSON.parse(fileContent);
    const moduleData = extractSections(jsonData);

    const sections = Object.entries(moduleData).map(([key, value], index) => {
      // Handle interleaved structure with type field
      let sectionTitle: string;
      if (value?.type === 'qna' && value?.questions && Array.isArray(value.questions)) {
        // For QnA sections with multiple questions, use a descriptive title
        sectionTitle = value.sectionKey 
          ? `QnA: ${value.sectionKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`
          : 'QnA Questions';
      } else {
        sectionTitle = value?.title || value?.question || key;
      }
      const content = value;
      
      return {
        sectionId: `${moduleId}-${index + 1}`,
        sectionTitle: sectionTitle,
        content: content,
      };
    });

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
