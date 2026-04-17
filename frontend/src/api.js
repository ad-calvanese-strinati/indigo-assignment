const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
const API_TOKEN = import.meta.env.VITE_API_TOKEN || "change-me";

function buildHeaders(extra = {}) {
  return {
    Authorization: `Bearer ${API_TOKEN}`,
    ...extra,
  };
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        message = payload.detail;
      }
    } catch {
      // Ignore JSON parsing failures and keep the fallback error message.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function fetchDocuments() {
  return request("/documents", {
    headers: buildHeaders(),
  });
}

export async function fetchTags() {
  return request("/tags", {
    headers: buildHeaders(),
  });
}

export async function uploadDocument({ file, tags }) {
  const body = new FormData();
  body.append("file", file);
  body.append("tags", tags.join(","));

  return request("/documents", {
    method: "POST",
    headers: buildHeaders(),
    body,
  });
}

export async function deleteDocument(documentId) {
  return request(`/documents/${documentId}`, {
    method: "DELETE",
    headers: buildHeaders(),
  });
}

export { API_BASE_URL };
