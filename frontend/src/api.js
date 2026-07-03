// Thin fetch wrappers around the backend API.
// Requests use relative /api paths, proxied to FastAPI by Vite in dev.

export async function getItems() {
  const res = await fetch("/api/items");
  if (!res.ok) throw new Error(`Failed to load items (${res.status})`);
  return res.json();
}

export async function setRating(id, rating) {
  const res = await fetch(`/api/items/${id}/rating`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating }),
  });
  if (!res.ok) throw new Error(`Failed to save rating (${res.status})`);
  return res.json();
}

export async function deleteItems(ids) {
  const res = await fetch("/api/items/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
  if (!res.ok) throw new Error(`Failed to delete items (${res.status})`);
  return res.json();
}
