const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "cloudrag_access_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function getStoredToken() {
  return getToken();
}

export function saveToken(token) {
  setToken(token);
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return text || null;
}

export async function apiFetch(path, options = {}) {
  const token = getToken();

  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await parseResponse(response);

  if (response.status === 401) {
    clearToken();
    window.dispatchEvent(new Event("cloudrag-auth-expired"));
  }

  if (!response.ok) {
    const message =
      typeof data === "object" && data?.detail
        ? data.detail
        : typeof data === "string" && data
          ? data
          : `Request failed with status ${response.status}.`;

    throw new Error(message);
  }

  return data;
}

export async function register(email, password) {
  const data = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  if (data?.access_token) {
    saveToken(data.access_token);
  }

  return data;
}

export async function login(email, password) {
  const data = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  if (data?.access_token) {
    saveToken(data.access_token);
  }

  return data;
}

export async function getCurrentUser() {
  return apiFetch("/auth/me");
}

export function logout() {
  clearToken();
  window.dispatchEvent(new Event("cloudrag-logout"));
}

export async function listDocuments() {
  return apiFetch("/documents");
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch("/documents", {
    method: "POST",
    body: formData,
  });
}

export async function deleteDocument(documentId) {
  return apiFetch(`/documents/${documentId}`, {
    method: "DELETE",
  });
}

export async function downloadDocument(documentId) {
  const token = getToken();

  const response = await fetch(
    `${API_URL}/documents/${documentId}/download`,
    {
      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    }
  );

  if (!response.ok) {
    let message = `Download failed with status ${response.status}.`;

    try {
      const data = await response.json();

      if (data?.detail) {
        message = data.detail;
      }
    } catch {
      // Keep the generic download error.
    }

    throw new Error(message);
  }

  const blob = await response.blob();

  const disposition =
    response.headers.get("Content-Disposition") || "";

  const filenameMatch = disposition.match(
    /filename\*=UTF-8''([^;]+)/i
  );

  const filename = filenameMatch
    ? decodeURIComponent(filenameMatch[1])
    : "document";

  const objectUrl = URL.createObjectURL(blob);

  try {
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

export async function searchDocuments(
  query,
  limit = 5,
  documentIds = []
) {
  return apiFetch("/search", {
    method: "POST",
    body: JSON.stringify({
      query,
      limit,
      document_ids: documentIds,
    }),
  });
}

export async function streamAskQuestion(
  question,
  limit = 3,
  documentIds = [],
  sessionId = null,
  onEvent
) {
  const token = getToken();

  const response = await fetch(`${API_URL}/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token
        ? { Authorization: `Bearer ${token}` }
        : {}),
    },
    body: JSON.stringify({
      question,
      limit,
      document_ids: documentIds,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;

    try {
      const data = await response.json();
      if (data?.detail) {
        message = data.detail;
      }
    } catch {
      // Keep the generic error.
    }

    if (response.status === 401) {
      clearToken();
      window.dispatchEvent(new Event("cloudrag-auth-expired"));
    }

    throw new Error(message);
  }

  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  function processEvent(rawEvent) {
    const lines = rawEvent.split("\n");
    let eventName = "message";
    let data = "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        data += line.slice(5).trim();
      }
    }

    if (!data) {
      return;
    }

    try {
      onEvent(eventName, JSON.parse(data));
    } catch {
      // Ignore malformed SSE events.
    }
  }

  while (true) {
    const { value, done } = await reader.read();

    buffer += decoder.decode(value || new Uint8Array(), {
      stream: !done,
    });

    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const event of events) {
      processEvent(event);
    }

    if (done) {
      break;
    }
  }

  if (buffer.trim()) {
    processEvent(buffer);
  }
}


export async function compareDocuments(documentIds) {
  return apiFetch("/documents/compare", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds }),
  });
}

export async function askQuestion(
  question,
  limit = 3,
  documentIds = [],
  sessionId = null
) {
  return apiFetch("/ask", {
    method: "POST",
    body: JSON.stringify({
      question,
      limit,
      document_ids: documentIds,
      session_id: sessionId,
    }),
  });
}

export async function listSessions() {
  return apiFetch("/sessions");
}

export async function createSession(title = "New Chat") {
  return apiFetch("/sessions", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function getSessionMessages(sessionId) {
  return apiFetch(`/sessions/${sessionId}/messages`);
}

export async function deleteSession(sessionId) {
  return apiFetch(`/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

export async function getHealth() {
  const response = await fetch(`${API_URL}/health`);

  const contentType =
    response.headers.get("content-type") || "";

  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new Error("Health check failed.");
  }

  return data;
}

export { API_URL };

export async function runEvaluation(cases, limit = 5) {
  return apiFetch("/evaluation/run", {
    method: "POST",
    body: JSON.stringify({ cases, limit }),
  });
}
