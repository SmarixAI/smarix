import { NextRequest, NextResponse } from "next/server";
import { readJsonFromS3WithFallback, writeJsonToS3 } from "../../../../components/offboarding/s3Utils";

export async function GET() {
  try {
    const possibleFiles = ["handover_tasks.json", "5employee_handovers.json"];

    const { data: jsonData, fileName: filePath } =
      await readJsonFromS3WithFallback(possibleFiles);

    // Transform data structure to match frontend expectations
    if (filePath.includes("handover_tasks.json")) {
      // Try to load users.json to map names to employeeIds
      let usersMap: Record<string, string> = {};
      try {
        const usersData = await readJsonFromS3WithFallback([
          "users.json",
          "Admin/users.json",
        ]);
        usersData.data.users?.forEach((user: any) => {
          if (user.employeeId && user.name) {
            usersMap[user.name.toLowerCase()] = user.employeeId;
          }
          if (user.employeeId && user.username) {
            usersMap[user.username.toLowerCase()] = user.employeeId;
          }
        });
      } catch (e) {
        console.log("Could not load users.json for mapping:", e);
      }

      const transformed = {
        employees: jsonData.employees.map((emp: any) => {
          const tasks = emp.handover_tasks?.tasks || [];
          const employeeName = emp.employee_name || emp.name || "";
          const employeeId =
            emp.employeeId ||
            emp.employee_id ||
            usersMap[employeeName.toLowerCase()] ||
            employeeName;

          return {
            employeeId: employeeId,
            employee_id: employeeId,
            name: employeeName,
            handovers: tasks.map((task: any, idx: number) => ({
              id: task.taskId || `HO${idx + 1}`,
              item: task.title || "",
              currentOwner: employeeName,
              newOwner: task.suggested_recipient || "",
              priority:
                (task.priority || "Medium").charAt(0).toUpperCase() +
                (task.priority || "Medium").slice(1).toLowerCase(),
              status: "Pending",
              ktType: task.knowledge_type || [],
              lastUpdated: new Date().toISOString().split("T")[0],
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
          "Cache-Control":
            "public, s-maxage=3600, stale-while-revalidate=86400",
        },
      });
    }

    return NextResponse.json(jsonData, {
      headers: {
        "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to load handovers data",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { employeeId, handoverId, priority } = body;

    if (!employeeId || !handoverId || !priority) {
      return NextResponse.json(
        { error: "Employee ID, Handover ID, and Priority are required" },
        { status: 400 },
      );
    }

    // Try to find the file
    const possibleFiles = ["handover_tasks.json", "5employee_handovers.json"];

    const { data: jsonData, fileName } =
      await readJsonFromS3WithFallback(possibleFiles);

    // Find employee
    const employeeIndex = jsonData.employees.findIndex(
      (emp: any) => emp.employeeId === employeeId,
    );

    if (employeeIndex === -1) {
      return NextResponse.json(
        { error: "Employee not found" },
        { status: 404 },
      );
    }

    // Find and update handover
    const handovers = jsonData.employees[employeeIndex].handovers || [];
    const handoverIndex = handovers.findIndex((h: any) => h.id === handoverId);

    if (handoverIndex === -1) {
      return NextResponse.json(
        { error: "Handover not found" },
        { status: 404 },
      );
    }

    // Update priority
    handovers[handoverIndex].priority = priority;

    // Write back to S3
    await writeJsonToS3(fileName, jsonData);

    return NextResponse.json(
      { success: true, handover: handovers[handoverIndex] },
      {
        headers: {
          "Cache-Control": "no-cache",
        },
      },
    );
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to update handover priority",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}
