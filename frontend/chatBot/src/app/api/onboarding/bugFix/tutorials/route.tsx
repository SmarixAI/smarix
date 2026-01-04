import { NextResponse } from 'next/server';
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
            // Try new structure: owner/repo/onboarding_bugfix_data/
            const newPath = path.join(basePath, owner, repoName, 'onboarding_bugfix_data', fileName);
            try {
              await fs.access(newPath);
              return newPath;
            } catch {
              // Try alternative: owner/repo/bugfix/
              const altPath = path.join(basePath, owner, repoName, 'bugfix', fileName);
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
              try {
                const ownerEntries = await fs.readdir(ownerPath, { withFileTypes: true });
                for (const repoEntry of ownerEntries) {
                  if (repoEntry.isDirectory()) {
                    // Try new structure: owner/repo/onboarding_bugfix_data/
                    const newPath = path.join(ownerPath, repoEntry.name, 'onboarding_bugfix_data', fileName);
                    try {
                      await fs.access(newPath);
                      return newPath;
                    } catch {
                      // Try alternative: owner/repo/bugfix/
                      const altPath = path.join(ownerPath, repoEntry.name, 'bugfix', fileName);
                      try {
                        await fs.access(altPath);
                        return altPath;
                      } catch {
                        continue;
                      }
                    }
                  }
                }
              } catch {
                // Not owner/repo structure, try flat
              }
              
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

    const filePath = await findFileInRepos(possibleBasePaths, 'onboarding_pr_tutorials.json', repo);
    
    if (!filePath) {
      return NextResponse.json(
        { error: 'PR tutorials file not found' },
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
      error: 'Failed to load PR tutorials',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}
