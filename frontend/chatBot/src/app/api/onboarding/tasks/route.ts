import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const employeeId = searchParams.get('employeeId');

    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding', 'employee_onboarding_tasks.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding', 'employee_onboarding_tasks.json'),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding', 'employee_onboarding_tasks.json'),
      path.join(process.cwd(), 'backend/data/Onboarding/employee_onboarding_tasks.json'),
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
        { error: 'Onboarding tasks file not found' },
        { status: 404 }
      );
    }

    const jsonData = JSON.parse(fileContent);

    // If employeeId is provided, return that employee's data, or default data if not found
    if (employeeId) {
      console.log('API - Looking for employeeId:', employeeId);
      console.log('API - Available employeeIds:', jsonData.employees?.map((emp: any) => emp.employeeId));
      
      let employee = jsonData.employees?.find((emp: any) => 
        emp.employeeId === employeeId ||
        emp.employee_id === employeeId ||
        String(emp.employeeId) === String(employeeId) ||
        String(emp.employee_id) === String(employeeId) ||
        emp.username === employeeId ||
        emp.name === employeeId
      );

      // If employee not found, return empty data structure with 0% progress
      if (!employee) {
        console.log('API - Employee not found, returning empty data structure for:', employeeId);
        
        // Get employee info from users.json if possible
        let employeeInfo = {
          employeeId: employeeId,
          username: employeeId,
          name: employeeId,
          status: 'onboard'
        };

        // Return empty onboarding structure
        return NextResponse.json({
          employee: employeeInfo,
          onboarding: {
            reading: {
              modules: []
            },
            qa: {
              modules: []
            },
            practice: {
              tasks: []
            },
            bugfix: {
              tutorials: [],
              challenges: [],
              coding_questions: []
            }
          }
        }, {
          headers: {
            'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
          },
        });
      }

      console.log('API - Returning onboarding data for:', employeeId);
      return NextResponse.json({
        employee: {
          ...employee,
          employeeId: employeeId
        },
        onboarding: employee.onboarding || {
          reading: { modules: [] },
          qa: { modules: [] },
          practice: { tasks: [] },
          bugfix: { tutorials: [], challenges: [], coding_questions: [] }
        }
      }, {
        headers: {
          'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
        },
      });
    }

    // Return all employees
    return NextResponse.json(jsonData, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load onboarding tasks data',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

