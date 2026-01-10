import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET() {
  try {
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', 'documentation_tasks.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', 'documentation_tasks.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', 'documentation_tasks.json'),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '6employee_documents.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '6employee_documents.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '6employee_documents.json'),
    ];

    let fileContent: string | null = null;
    let filePath: string | null = null;

    for (const p of possiblePaths) {
      try {
        await fs.access(p);
        fileContent = await fs.readFile(p, 'utf-8');
        filePath = p;
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

    // Transform data structure to match frontend expectations
    // If file is documentation_tasks.json, transform it
    if (filePath && filePath.includes('documentation_tasks.json')) {
      // Try to load users.json to map names to employeeIds
      let usersMap: Record<string, string> = {};
      try {
        const usersPaths = [
          path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'users.json'),
          path.join(process.cwd(), '..', 'backend', 'data', 'Admin', 'users.json'),
          path.join(process.cwd(), 'backend', 'data', 'Admin', 'users.json'),
        ];
        for (const usersPath of usersPaths) {
          try {
            const usersContent = await fs.readFile(usersPath, 'utf-8');
            const usersData = JSON.parse(usersContent);
            usersData.users?.forEach((user: any) => {
              if (user.employeeId && user.name) {
                usersMap[user.name.toLowerCase()] = user.employeeId;
              }
              if (user.employeeId && user.username) {
                usersMap[user.username.toLowerCase()] = user.employeeId;
              }
            });
            break;
          } catch {
            continue;
          }
        }
      } catch (e) {
        console.log('Could not load users.json for mapping:', e);
      }

      const transformed = {
        employees: jsonData.employees.map((emp: any) => {
          const tasks = emp.documentation_tasks?.tasks || [];
          const employeeName = emp.employee_name || emp.name || '';
          // Try to find employeeId from users.json by name or username
          const employeeId = emp.employeeId || 
                            emp.employee_id || 
                            usersMap[employeeName.toLowerCase()] || 
                            employeeName;
          
          return {
            employeeId: employeeId,
            employee_id: employeeId,
            name: employeeName,
            documents: tasks.map((task: any, idx: number) => ({
              id: task.taskId || `DOC${idx + 1}`,
              name: task.title || '',
              status: 'Missing',
              priority: (task.priority || 'Medium').charAt(0).toUpperCase() + (task.priority || 'Medium').slice(1).toLowerCase(),
              owner: employeeName,
              aiFollowUp: task.ai_analyzed || false,
              lastUpdated: new Date().toISOString().split('T')[0],
              description: task.description,
              questions: task.questions,
              reference: task.reference,
            })),
          };
        }),
      };
      return NextResponse.json(transformed, {
        headers: {
          'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
        },
      });
    }

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
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', 'documentation_tasks.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', 'documentation_tasks.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', 'documentation_tasks.json'),
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

