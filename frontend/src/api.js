const runtimeConfig = window.__APP_CONFIG__ || {};

const API_BASE_URL =
  runtimeConfig.API_BASE_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000/api";
const API_TOKEN =
  runtimeConfig.API_TOKEN ||
  import.meta.env.VITE_API_TOKEN ||
  "change-me";

function buildHeaders(extra = {}) {
  return {
    Authorization: `Bearer ${API_TOKEN}`,
    ...extra,
  };
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        message = payload.detail;
      }
    } catch {
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function fetchDocuments() {
  return apiFetch("/documents", {
    headers: buildHeaders(),
  });
}

export async function fetchTags() {
  return apiFetch("/tags", {
    headers: buildHeaders(),
  });
}

export async function uploadDocument({ file, tags }) {
  const body = new FormData();
  body.append("file", file);
  body.append("tags", tags.join(","));

  return apiFetch("/documents", {
    method: "POST",
    headers: buildHeaders(),
    body,
  });
}

export async function deleteDocument(documentId) {
  return apiFetch(`/documents/${documentId}`, {
    method: "DELETE",
    headers: buildHeaders(),
  });
}

export { API_BASE_URL };
