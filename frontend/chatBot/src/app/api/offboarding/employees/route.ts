import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

// Helper function to add employee to users.json
async function addEmployeeToUsers(employee: any) {
  try {
    const employeeName = employee.name?.trim();
    const employeeId = employee.employee_id || employee.id;
    
    if (!employeeName) {
      console.warn('Cannot add employee to users.json: name is missing');
      return;
    }

    // Find users.json file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'users.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Admin', 'users.json'),
      path.join(process.cwd(), 'backend', 'data', 'Admin', 'users.json'),
    ];

    let usersFilePath: string | null = null;

    for (const p of possiblePaths) {
      try {
        await fs.access(p);
        usersFilePath = p;
        break;
      } catch {
        continue;
      }
    }

    if (!usersFilePath) {
      // Create the file if it doesn't exist
      const defaultPath = path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'users.json');
      usersFilePath = defaultPath;
      const defaultUsers = {
        users: [
          {
            username: "admin",
            password: "admin",
            role: "admin",
            employeeId: null
          }
        ]
      };
      await fs.mkdir(path.dirname(usersFilePath), { recursive: true });
      await fs.writeFile(usersFilePath, JSON.stringify(defaultUsers, null, 2), 'utf-8');
    }

    // Read existing users
    const usersContent = await fs.readFile(usersFilePath, 'utf-8');
    const usersData = JSON.parse(usersContent);

    // Check if user already exists
    const existingUserIndex = usersData.users.findIndex((u: any) => 
      u.username?.toLowerCase() === employeeName.toLowerCase() ||
      (u.employeeId && employeeId && u.employeeId === employeeId)
    );

    if (existingUserIndex !== -1) {
      // Update existing user if needed
      const existingUser = usersData.users[existingUserIndex];
      if (existingUser.role !== 'employee') {
        existingUser.role = 'employee';
      }
      if (!existingUser.employeeId && employeeId) {
        existingUser.employeeId = employeeId;
      }
      if (!existingUser.name) {
        existingUser.name = employeeName;
      }
      if (existingUser.password !== employeeName) {
        existingUser.password = employeeName;
      }
      if (existingUser.username !== employeeName) {
        existingUser.username = employeeName;
      }
    } else {
      // Add new employee user
      const newUser = {
        username: employeeName,
        password: employeeName, // Password same as username (employee's name)
        role: "employee",
        employeeId: employeeId || null,
        name: employeeName
      };
      usersData.users.push(newUser);
    }

    // Write back to users.json
    await fs.writeFile(usersFilePath, JSON.stringify(usersData, null, 2), 'utf-8');
    console.log(`Added/updated employee "${employeeName}" to users.json`);
  } catch (error) {
    console.error('Error adding employee to users.json:', error);
    // Don't throw - this is a side effect, shouldn't break the main flow
  }
}

export async function GET() {
  try {
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '1employees_with_ids.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '1employees_with_ids.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '1employees_with_ids.json'),
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
        { error: 'Employees file not found' },
        { status: 404 }
      );
    }

    const jsonData = JSON.parse(fileContent);

    // Transform data to match frontend expectations
    const employees = (jsonData.employees || []).map((emp: any) => {
      const employeeId = emp.employee_id || emp.id;
      // Normalize lastDay: convert string "null" to actual null, and handle empty strings
      let lastDay = emp.lastDay;
      if (lastDay === 'null' || lastDay === null || lastDay === '' || lastDay === undefined) {
        lastDay = null;
      }
      
      // Determine status: if status is explicitly "active" and lastDay is null, keep as active
      // Otherwise, if lastDay exists and is valid, status should be "leaving"
      let status = emp.status;
      if (status === 'active' && !lastDay) {
        status = 'active';
      } else if (lastDay && lastDay !== 'null') {
        status = 'leaving';
      } else if (emp.status === 'leaving') {
        status = 'leaving';
      } else {
        status = 'active';
      }
      
      return {
        id: employeeId,
        employeeId: employeeId, // Include both for compatibility
        name: emp.name,
        role: emp.role,
        risk: emp.risk,
        status: status,
        lastDay: lastDay,
      };
    });

    return NextResponse.json(
      { employees },
      {
        headers: {
          'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
        },
      }
    );
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load employees data',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { employeeId, status, lastDay } = body;

    if (!employeeId) {
      return NextResponse.json(
        { error: 'Employee ID is required' },
        { status: 400 }
      );
    }

    // Find the file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '1employees_with_ids.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '1employees_with_ids.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '1employees_with_ids.json'),
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
        { error: 'Employees file not found' },
        { status: 404 }
      );
    }

    // Read current data
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(fileContent);

    // Update employee
    const employeeIndex = jsonData.employees.findIndex(
      (emp: any) => emp.employee_id === employeeId || emp.id === employeeId
    );

    if (employeeIndex === -1) {
      return NextResponse.json(
        { error: 'Employee not found' },
        { status: 404 }
      );
    }

    // Get employee data before updating (for users.json)
    const employeeData = { ...jsonData.employees[employeeIndex] };

    // Update the employee
    // When marking as leaving, ALWAYS set status to 'leaving' and update lastDay
    if (status === 'leaving') {
      jsonData.employees[employeeIndex].status = 'leaving';
      if (lastDay !== undefined && lastDay !== null && lastDay !== 'null' && lastDay !== '') {
        jsonData.employees[employeeIndex].lastDay = lastDay;
      }
    } else if (status === 'active') {
      // When marking as active, clear lastDay and set status to active
      jsonData.employees[employeeIndex].status = 'active';
      jsonData.employees[employeeIndex].lastDay = null;
    } else if (status !== undefined) {
      // For other status updates
      jsonData.employees[employeeIndex].status = status;
      if (lastDay !== undefined && status !== 'leaving') {
        if (lastDay === null || lastDay === 'null' || lastDay === '') {
          jsonData.employees[employeeIndex].lastDay = null;
        } else {
          jsonData.employees[employeeIndex].lastDay = lastDay;
        }
      }
    } else if (lastDay !== undefined && lastDay !== null && lastDay !== 'null' && lastDay !== '') {
      // If only lastDay is provided without status, and lastDay is set, mark as leaving
      jsonData.employees[employeeIndex].lastDay = lastDay;
      jsonData.employees[employeeIndex].status = 'leaving';
    } else if (lastDay === null || lastDay === 'null' || lastDay === '') {
      // If lastDay is cleared, set status to active
      jsonData.employees[employeeIndex].lastDay = null;
      jsonData.employees[employeeIndex].status = 'active';
    }

    // Write back to file
    await fs.writeFile(
      filePath,
      JSON.stringify(jsonData, null, 2),
      'utf-8'
    );

    // Add employee to users.json when marked as leaving
    if (status === 'leaving') {
      await addEmployeeToUsers(employeeData);
    }

    // Return updated employee
    const updatedEmployee = jsonData.employees[employeeIndex];
    const transformedEmployee = {
      id: updatedEmployee.employee_id || updatedEmployee.id,
      employeeId: updatedEmployee.employee_id || updatedEmployee.id,
      name: updatedEmployee.name,
      role: updatedEmployee.role,
      risk: updatedEmployee.risk,
      status: updatedEmployee.lastDay ? 'leaving' : (updatedEmployee.status === 'leaving' ? 'leaving' : 'active'),
      lastDay: updatedEmployee.lastDay,
    };

    return NextResponse.json(
      { employee: transformedEmployee },
      {
        headers: {
          'Cache-Control': 'no-cache',
        },
      }
    );
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to update employee',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

