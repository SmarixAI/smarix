export async function fetchProjectStructure(repoName: string) {
  const res = await fetch(
    `http://localhost:8000/impact/project-structure/${repoName}`
  );

  if (!res.ok) {
    throw new Error("Failed to fetch project structure");
  }

  return res.json();
}