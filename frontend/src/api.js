// Thin fetch wrappers around the backend API.
// Requests use relative /api paths, proxied to FastAPI by Vite in dev.

// On Render's free tier the instance spins down after ~15 min idle; the first
// request then hits the edge and gets a 404/502/503 with a *plain-text* body
// (e.g. "Not Found", header `x-render-routing: no-server`) while the container
// wakes, which takes up to ~50s. FastAPI's own errors are always JSON, so we
// retry only the plain-text edge responses (and network errors) and never mask
// a genuine app error like a 404 for a missing item.

const WAKE_TIMEOUT_MS = 60_000;
const RETRY_DELAY_MS = 2_000;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function isColdStart(res) {
  // Edge/proxy responses while the instance wakes: not JSON.
  if (res.status === 502 || res.status === 503 || res.status === 504) return true;
  if (res.status === 404) {
    const type = res.headers.get("content-type") || "";
    return !type.includes("application/json");
  }
  return false;
}

// fetch that transparently rides out a Render cold start.
async function wakeFetch(input, init) {
  const deadline = Date.now() + WAKE_TIMEOUT_MS;
  let lastErr;
  while (true) {
    try {
      const res = await fetch(input, init);
      if (isColdStart(res) && Date.now() < deadline) {
        await sleep(RETRY_DELAY_MS);
        continue;
      }
      return res;
    } catch (err) {
      // Network-level failure (instance not yet reachable): retry until deadline.
      lastErr = err;
      if (Date.now() >= deadline) throw lastErr;
      await sleep(RETRY_DELAY_MS);
    }
  }
}

export async function getItems() {
  const res = await wakeFetch("/api/items");
  if (!res.ok) throw new Error(`Failed to load items (${res.status})`);
  return res.json();
}

export async function setRating(id, rating) {
  const res = await wakeFetch(`/api/items/${id}/rating`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating }),
  });
  if (!res.ok) throw new Error(`Failed to save rating (${res.status})`);
  return res.json();
}

export async function deleteItems(ids) {
  const res = await wakeFetch("/api/items/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
  if (!res.ok) throw new Error(`Failed to delete items (${res.status})`);
  return res.json();
}
