export async function fetchImpactMetadata(
  repoId: string,
  commitHash: string
) {
  const res = await fetch(
    `http://localhost:8000/impact/${repoId}/${commitHash}`
  );

  if (!res.ok) {
    throw new Error("Failed to fetch impact metadata");
  }

  return res.json();
}