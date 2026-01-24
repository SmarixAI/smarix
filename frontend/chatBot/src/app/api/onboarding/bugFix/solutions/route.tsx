import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const repo = searchParams.get('repo');

    // Helper function to find file in repo folders
    const findFileInRepos = async (basePaths: string[], fileName: string, repo?: string | null): Promise<string | null> => {
      for (const basePath of basePaths) {
        try {
          // If repo is provided, try owner/repo structure first
          if (repo) {
            const [owner, repoName] = repo.split('/');
            // Try bugfix/ folder first (most common location)
            const bugfixPath = path.join(basePath, owner, repoName, 'bugfix', fileName);
            try {
              await fs.access(bugfixPath);
              return bugfixPath;
            } catch {
              // Try new structure: owner/repo/onboarding_bugfix_data/
              const newPath = path.join(basePath, owner, repoName, 'onboarding_bugfix_data', fileName);
              try {
                await fs.access(newPath);
                return newPath;
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
              try {
                const ownerEntries = await fs.readdir(ownerPath, { withFileTypes: true });
                for (const repoEntry of ownerEntries) {
                  if (repoEntry.isDirectory()) {
                    // Try bugfix/ folder first (most common location)
                    const bugfixPath = path.join(ownerPath, repoEntry.name, 'bugfix', fileName);
                    try {
                      await fs.access(bugfixPath);
                      return bugfixPath;
                    } catch {
                      // Try new structure: owner/repo/onboarding_bugfix_data/
                      const newPath = path.join(ownerPath, repoEntry.name, 'onboarding_bugfix_data', fileName);
                      try {
                        await fs.access(newPath);
                        return newPath;
                      } catch {
                        continue;
                      }
                    }
                  }
                }
              } catch {
                // Not owner/repo structure, try flat
              }
              
              // Try flat repo structure: repo_name/bugfix/ first
              const flatBugfixPath = path.join(ownerPath, entry.name, 'bugfix', fileName);
              try {
                await fs.access(flatBugfixPath);
                return flatBugfixPath;
              } catch {
                // Try flat repo structure: repo_name/onboarding_bugfix_data/
                const flatPath = path.join(ownerPath, entry.name, 'onboarding_bugfix_data', fileName);
                try {
                  await fs.access(flatPath);
                  return flatPath;
                } catch {
                  continue;
                }
              }
            }
          }
          
          // Try old structure (direct file)
          const oldPath = path.join(basePath, 'onboarding_bugfix_data', fileName);
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

    const filePath = await findFileInRepos(possibleBasePaths, 'onboarding_challenge_solution.json', repo);
    
    if (!filePath) {
      return NextResponse.json(
        { error: 'Challenge solution file not found' },
        { status: 404 }
      );
    }

    const fileContent = await fs.readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(fileContent);

    return NextResponse.json(jsonData, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load challenge solution data',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

