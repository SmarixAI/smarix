import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET() {
  try {
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '6employee_documents.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '6employee_documents.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '6employee_documents.json'),
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
        { error: 'Documents file not found' },
        { status: 404 }
      );
    }

    const jsonData = JSON.parse(fileContent);

    return NextResponse.json(jsonData, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load documents data',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { employeeId, documentId, priority, status } = body;

    if (!employeeId || !documentId) {
      return NextResponse.json(
        { error: 'Employee ID and Document ID are required' },
        { status: 400 }
      );
    }

    if (!priority && !status) {
      return NextResponse.json(
        { error: 'Either Priority or Status must be provided' },
        { status: 400 }
      );
    }

    // Find the file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '6employee_documents.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '6employee_documents.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '6employee_documents.json'),
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
        { error: 'Documents file not found' },
        { status: 404 }
      );
    }

    // Read current data
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(fileContent);

    // Find employee
    const employeeIndex = jsonData.employees.findIndex(
      (emp: any) => emp.employeeId === employeeId
    );

    if (employeeIndex === -1) {
      return NextResponse.json(
        { error: 'Employee not found' },
        { status: 404 }
      );
    }

    // Find and update document
    const documents = jsonData.employees[employeeIndex].documents || [];
    const documentIndex = documents.findIndex((d: any) => d.id === documentId);

    if (documentIndex === -1) {
      return NextResponse.json(
        { error: 'Document not found' },
        { status: 404 }
      );
    }

    // Update priority and/or status
    if (priority !== undefined) {
      documents[documentIndex].priority = priority;
    }
    if (status !== undefined) {
      documents[documentIndex].status = status;
    }

    // Write back to file
    await fs.writeFile(
      filePath,
      JSON.stringify(jsonData, null, 2),
      'utf-8'
    );

    return NextResponse.json(
      { success: true, document: documents[documentIndex] },
      {
        headers: {
          'Cache-Control': 'no-cache',
        },
      }
    );
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to update document priority',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

