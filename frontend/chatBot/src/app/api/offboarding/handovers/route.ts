import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET() {
  try {
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', 'handover_tasks.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', 'handover_tasks.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', 'handover_tasks.json'),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '5employee_handovers.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '5employee_handovers.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '5employee_handovers.json'),
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
        { error: 'Handovers file not found' },
        { status: 404 }
      );
    }

    const jsonData = JSON.parse(fileContent);

    // Transform data structure to match frontend expectations
    // If file is handover_tasks.json, transform it
    if (filePath && filePath.includes('handover_tasks.json')) {
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
          const tasks = emp.handover_tasks?.tasks || [];
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
            handovers: tasks.map((task: any, idx: number) => ({
              id: task.taskId || `HO${idx + 1}`,
              item: task.title || '',
              currentOwner: employeeName,
              newOwner: task.suggested_recipient || '',
              priority: (task.priority || 'Medium').charAt(0).toUpperCase() + (task.priority || 'Medium').slice(1).toLowerCase(),
              status: 'Pending',
              ktType: task.knowledge_type || [],
              lastUpdated: new Date().toISOString().split('T')[0],
              description: task.description,
              questions: task.questions,
              reference: task.reference,
              suggested_recipient: task.suggested_recipient,
              suggested_recipient_reason: task.suggested_recipient_reason,
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
      error: 'Failed to load handovers data',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { employeeId, handoverId, priority } = body;

    if (!employeeId || !handoverId || !priority) {
      return NextResponse.json(
        { error: 'Employee ID, Handover ID, and Priority are required' },
        { status: 400 }
      );
    }

    // Find the file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', 'handover_tasks.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', 'handover_tasks.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', 'handover_tasks.json'),
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '5employee_handovers.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '5employee_handovers.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '5employee_handovers.json'),
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
        { error: 'Handovers file not found' },
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

    // Find and update handover
    const handovers = jsonData.employees[employeeIndex].handovers || [];
    const handoverIndex = handovers.findIndex((h: any) => h.id === handoverId);

    if (handoverIndex === -1) {
      return NextResponse.json(
        { error: 'Handover not found' },
        { status: 404 }
      );
    }

    // Update priority
    handovers[handoverIndex].priority = priority;

    // Write back to file
    await fs.writeFile(
      filePath,
      JSON.stringify(jsonData, null, 2),
      'utf-8'
    );

    return NextResponse.json(
      { success: true, handover: handovers[handoverIndex] },
      {
        headers: {
          'Cache-Control': 'no-cache',
        },
      }
    );
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to update handover priority',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

