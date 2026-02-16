import { NextRequest, NextResponse } from 'next/server';
import { readJsonFromS3WithFallback, writeJsonToS3 } from '../../../../components/offboarding/s3Utils';

export async function GET() {
  try {
    const possibleFiles = [
      'documentation_tasks.json',
    ];

    const { data: jsonData, fileName: filePath } = await readJsonFromS3WithFallback(possibleFiles);

    // Transform data structure to match frontend expectations
    if (filePath.includes('documentation_tasks.json')) {
      // Try to load users.json to map names to employeeIds
      let usersMap: Record<string, string> = {};
      try {
        const usersData = await readJsonFromS3WithFallback(['users.json', 'Admin/users.json']);
        usersData.data.users?.forEach((user: any) => {
          if (user.employeeId && user.name) {
            usersMap[user.name.toLowerCase()] = user.employeeId;
          }
          if (user.employeeId && user.username) {
            usersMap[user.username.toLowerCase()] = user.employeeId;
          }
        });
      } catch (e) {
        console.log('Could not load users.json for mapping:', e);
      }

      const transformed = {
        employees: jsonData.employees.map((emp: any) => {
          const tasks = emp.documentation_tasks?.tasks || [];
          const employeeName = emp.employee_name || emp.name || '';
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
    const possibleFiles = [
      'documentation_tasks.json',
      '6employee_documents.json',
    ];

    const { data: jsonData, fileName } = await readJsonFromS3WithFallback(possibleFiles);

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

    // Write back to S3
    await writeJsonToS3(fileName, jsonData);

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