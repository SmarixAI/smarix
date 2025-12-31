import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

function getUsersFilePath(): string | null {
  const possiblePaths = [
    path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'users.json'),
    path.join(process.cwd(), '..', 'backend', 'data', 'Admin', 'users.json'),
    path.join(process.cwd(), 'backend', 'data', 'Admin', 'users.json'),
  ];

  for (const p of possiblePaths) {
    try {
      // Check if file exists synchronously (we'll use async access later)
      return p;
    } catch {
      continue;
    }
  }
  return null;
}

export async function GET() {
  try {
    // Find the file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'users.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Admin', 'users.json'),
      path.join(process.cwd(), 'backend', 'data', 'Admin', 'users.json'),
    ];

    let filePath: string | null = null;

    for (const p of possiblePaths) {
      try {
        await fs.access(p);
        filePath = p;
        break;
      } catch {
        continue;
      }
    }

    if (!filePath) {
      return NextResponse.json(
        { error: 'Users file not found' },
        { status: 404 }
      );
    }

    // Read current data
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(fileContent);

    return NextResponse.json(jsonData, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    console.error('Error fetching users:', error);
    return NextResponse.json(
      { error: 'Failed to load users data' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, status, lastDay } = body;

    if (!username) {
      return NextResponse.json(
        { error: 'Username is required' },
        { status: 400 }
      );
    }

    // Find the file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'users.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Admin', 'users.json'),
      path.join(process.cwd(), 'backend', 'data', 'Admin', 'users.json'),
    ];

    let filePath: string | null = null;

    for (const p of possiblePaths) {
      try {
        await fs.access(p);
        filePath = p;
        break;
      } catch {
        continue;
      }
    }

    if (!filePath) {
      return NextResponse.json(
        { error: 'Users file not found' },
        { status: 404 }
      );
    }

    // Read current data
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(fileContent);

    // Find the user
    const userIndex = jsonData.users.findIndex((u: any) => u.username === username);
    
    if (userIndex === -1) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Update user
    if (status !== undefined) {
      jsonData.users[userIndex].status = status;
    }
    
    if (lastDay !== undefined) {
      // Normalize lastDay: convert string "null" to actual null
      if (lastDay === 'null' || lastDay === null || lastDay === '') {
        jsonData.users[userIndex].lastDay = null;
      } else {
        jsonData.users[userIndex].lastDay = lastDay;
      }
    }

    // Write back to file
    await fs.writeFile(filePath, JSON.stringify(jsonData, null, 2), 'utf-8');

    return NextResponse.json({
      success: true,
      user: jsonData.users[userIndex]
    });
  } catch (error) {
    console.error('Error updating user:', error);
    return NextResponse.json(
      { error: 'Failed to update user' },
      { status: 500 }
    );
  }
}

