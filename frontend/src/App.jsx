import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import {
  apiFetch,
  API_URL,
  clearToken,
  getCurrentUser,
  getStoredToken,
  saveToken,
  getHealth,
  downloadDocument,
} from "./api";

function formatFileSize(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const now = new Date();

  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });
  }

  return date.toLocaleDateString([], {
    month: "short",
    day: "numeric",
  });
}

function App() {
  const [token, setToken] = useState(() => getStoredToken());
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authMode, setAuthMode] = useState("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authSubmitting, setAuthSubmitting] = useState(false);

  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionMessages, setSessionMessages] = useState([]);

  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [creatingSession, setCreatingSession] = useState(false);
  const [deletingSession, setDeletingSession] = useState(false);

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");

  const [documents, setDocuments] = useState([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deletingDocuments, setDeletingDocuments] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");

const [knowledgeOpen, setKnowledgeOpen] = useState(false);
const [systemOpen, setSystemOpen] = useState(false);
const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [health, setHealth] = useState(null);

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("cloudrag-theme") || "light";
  });

  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  async function handleAuthSubmit(event) {
    event.preventDefault();

    const email = authEmail.trim().toLowerCase();
    const password = authPassword;

    if (!email || !password) {
      setAuthError("Email and password are required.");
      return;
    }

    setAuthSubmitting(true);
    setAuthError("");

    try {
      const endpoint =
        authMode === "login"
          ? "/auth/login"
          : "/auth/register";

      const data = await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
        }),
      });

      saveToken(data.access_token);
      setToken(data.access_token);
      setAuthPassword("");
      setAuthError("");
    } catch (error) {
      setAuthError(
        error.message ||
          (authMode === "login"
            ? "Login failed."
            : "Registration failed.")
      );
    } finally {
      setAuthSubmitting(false);
    }
  }

  function logout() {
    clearToken();
    setToken(null);
    setUser(null);
    setSessions([]);
    setCurrentSessionId(null);
    setSessionMessages([]);
    setDocuments([]);
    setSelectedDocumentIds([]);
    setSearchResults([]);
    setQuestion("");
    setAskError("");
    setUploadStatus("");
    setAuthError("");
    setAuthPassword("");
  }

  async function loadSessions(selectLatest = true) {
    try {
      const data = await apiFetch("/sessions");
    
      setSessions(data);
    
      if (data.length === 0) {
        await createSession();
        return;
      }
    
      if (
        selectLatest &&
        (!currentSessionId ||
          !data.some(
            (session) => session.id === currentSessionId
          ))
      ) {
        await loadSession(data[0].id);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoadingSessions(false);
    }
  }

async function createSession() {
  if (creatingSession) {
    return null;
  }

  setCreatingSession(true);

  try {
    const data = await apiFetch("/sessions", {
      method: "POST",
      body: JSON.stringify({
        title: "New Chat",
      }),
    });

    setSessions((current) => [
      data,
      ...current.filter(
        (session) => session.id !== data.id
      ),
    ]);

    setCurrentSessionId(data.id);
    setSessionMessages([]);
    setQuestion("");
    setAskError("");

    return data.id;
  } catch (error) {
    setAskError(error.message);
    return null;
  } finally {
    setCreatingSession(false);
  }
}

async function loadSession(sessionId) {
  setCurrentSessionId(sessionId);
  setLoadingMessages(true);
  setAskError("");

  try {
    const data = await apiFetch(
      `/sessions/${sessionId}/messages`
    );

    setSessionMessages(data);
  } catch (error) {
    setSessionMessages([]);
    setAskError(error.message);
  } finally {
    setLoadingMessages(false);
  }
}

async function deleteCurrentSession() {
  if (!currentSessionId || deletingSession) {
    return;
  }

  const confirmed = window.confirm(
    "Delete this conversation?"
  );

  if (!confirmed) {
    return;
  }

  setDeletingSession(true);

  try {
    await apiFetch(
      `/sessions/${currentSessionId}`,
      {
        method: "DELETE",
      }
    );

    const remaining = sessions.filter(
      (session) => session.id !== currentSessionId
    );

    setSessions(remaining);

    if (remaining.length > 0) {
      await loadSession(remaining[0].id);
    } else {
      await createSession();
    }
  } catch (error) {
    setAskError(error.message);
  } finally {
    setDeletingSession(false);
  }
}

async function loadDocuments() {
  setLoadingDocuments(true);

  try {
    const data = await apiFetch("/documents");

    setDocuments(data);

    setSelectedDocumentIds((current) =>
      current.filter((id) =>
        data.some(
          (document) => document.id === id
        )
      )
    );
  } catch (error) {
    console.error(error);
  } finally {
    setLoadingDocuments(false);
  }
}

async function uploadDocument() {
  if (!file) {
    setUploadStatus("Choose a document first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  setUploading(true);
  setUploadStatus("");

  try {
    const data = await apiFetch("/documents", {
      method: "POST",
      body: formData,
    });

    setUploadStatus(
      `${data.filename} uploaded successfully.`
    );

    setFile(null);

    const fileInput =
      document.getElementById("document-upload");

    if (fileInput) {
      fileInput.value = "";
    }

    await loadDocuments();
  } catch (error) {
    setUploadStatus(`Error: ${error.message}`);
  } finally {
    setUploading(false);
  }
}

  async function handleDownloadDocument(documentId) {
    try {
      await downloadDocument(documentId);
    } catch (error) {
      window.alert(`Download failed: ${error.message}`);
    }
  }

  function toggleDocument(documentId) {
    setSelectedDocumentIds((current) => {
      if (current.includes(documentId)) {
        return current.filter((id) => id !== documentId);
      }

      return [...current, documentId];
    });
  }

  function toggleSelectAll() {
    if (
      documents.length > 0 &&
      selectedDocumentIds.length === documents.length
    ) {
      setSelectedDocumentIds([]);
      return;
    }

    setSelectedDocumentIds(
      documents.map((document) => document.id)
    );
  }

async function deleteSelectedDocuments() {
  if (
    selectedDocumentIds.length === 0 ||
    deletingDocuments
  ) {
    return;
  }

  const confirmed = window.confirm(
    `Delete ${selectedDocumentIds.length} selected document(s)?`
  );

  if (!confirmed) {
    return;
  }

  setDeletingDocuments(true);

  try {
    for (const documentId of selectedDocumentIds) {
      await apiFetch(`/documents/${documentId}`, {
        method: "DELETE",
      });
    }

    setSelectedDocumentIds([]);
    await loadDocuments();
  } catch (error) {
    window.alert(`Delete failed: ${error.message}`);
  } finally {
    setDeletingDocuments(false);
  }
}

async function searchDocuments() {
  if (!query.trim()) {
    return;
  }

  setSearching(true);
  setSearchError("");

  try {
    const data = await apiFetch("/search", {
      method: "POST",
      body: JSON.stringify({
        query,
        limit: 5,
        document_ids: selectedDocumentIds,
      }),
    });

    setSearchResults(data);
  } catch (error) {
    setSearchResults([]);
    setSearchError(error.message);
  } finally {
    setSearching(false);
  }
}
async function loadHealth() {
  try {
    const data = await getHealth();
    setHealth(data);
  } catch {
    setHealth({
      status: "degraded",
      dependencies: {
        database: "unavailable"
      },
    });
  }
}

async function askQuestion() {
  const trimmedQuestion = question.trim();

  if (!trimmedQuestion || asking) {
    return;
  }

  let sessionId = currentSessionId;

  if (!sessionId) {
    sessionId = await createSession();

    if (!sessionId) {
      return;
    }
  }

  const temporaryUserMessage = {
    id: `temp-user-${Date.now()}`,
    role: "user",
    content: trimmedQuestion,
    created_at: new Date().toISOString(),
    temporary: true,
  };

  setSessionMessages((current) => [
    ...current,
    temporaryUserMessage,
  ]);

  setQuestion("");
  setAskError("");
  setAsking(true);

  try {
    const data = await apiFetch("/ask", {
      method: "POST",
      body: JSON.stringify({
        question: trimmedQuestion,
        limit: 3,
        document_ids: selectedDocumentIds,
        session_id: sessionId,
      }),
    });

    setCurrentSessionId(data.session_id);

    await loadSession(data.session_id);
    await refreshSessionList(data.session_id);
  } catch (error) {
    setSessionMessages((current) =>
      current.filter(
        (message) =>
          message.id !== temporaryUserMessage.id
      )
    );

    setAskError(error.message);
  } finally {
    setAsking(false);
  }
}

 async function refreshSessionList(activeSessionId) {
  try {
    const data = await apiFetch("/sessions");

    setSessions(data);

    if (activeSessionId) {
      setCurrentSessionId(activeSessionId);
    }
  } catch (error) {
    console.error(error);
  }
}
  function handleComposerKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      askQuestion();
    }
  }

  function resizeTextarea() {
    if (!textareaRef.current) {
      return;
    }

    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height = `${Math.min(
      textareaRef.current.scrollHeight,
      180
    )}px`;
  }

  useEffect(() => {
    function handleUnauthorized() {
      logout();
    }

    window.addEventListener("cloudrag:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener(
        "cloudrag:unauthorized",
        handleUnauthorized
      );
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function validateAuthentication() {
      if (!token) {
        if (!cancelled) {
          setUser(null);
          setAuthLoading(false);
        }
        return;
      }

      setAuthLoading(true);

      try {
        const currentUser = await getCurrentUser();
        if (!cancelled) {
          setUser(currentUser);
        }
      } catch (error) {
        if (!cancelled) {
          clearToken();
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setAuthLoading(false);
        }
      }
    }

    validateAuthentication();

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!user) {
      return undefined;
    }

    loadSessions();
    loadDocuments();
    loadHealth();

    const interval = setInterval(loadHealth, 30000);

    return () => clearInterval(interval);
  }, [user]);


  useEffect(() => {
  localStorage.setItem("cloudrag-theme", theme);
  }, [theme]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [sessionMessages, asking]);

  useEffect(() => {
    resizeTextarea();
  }, [question]);

  const currentSession = useMemo(
    () =>
      sessions.find(
        (session) => session.id === currentSessionId
      ),
    [sessions, currentSessionId]
  );

  const selectedDocuments = useMemo(
    () =>
      documents.filter((document) =>
        selectedDocumentIds.includes(document.id)
      ),
    [documents, selectedDocumentIds]
  );

  const allSelected =
    documents.length > 0 &&
    selectedDocumentIds.length === documents.length;

  const systemHealthy =
  health?.status === "ok" ||
  health?.dependencies?.database === "ok";

  if (authLoading) {
    return (
      <main
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "#f7f8fa",
          color: "#1f2937",
          fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              display: "grid",
              placeItems: "center",
              margin: "0 auto 16px",
              background: "#111827",
              color: "white",
              fontSize: 24,
              fontWeight: 700,
            }}
          >
            C
          </div>
          <strong style={{ fontSize: 18 }}>CloudRAG</strong>
          <div style={{ marginTop: 8, color: "#6b7280" }}>Loading...</div>
        </div>
      </main>
    );
  }

  if (!user) {
    return (
      <main
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          padding: 24,
          background: "#f7f8fa",
          color: "#1f2937",
          fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
        }}
      >
        <section
          style={{
            width: "min(420px, 100%)",
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: 20,
            padding: 32,
            boxShadow: "0 18px 50px rgba(15, 23, 42, 0.08)",
          }}
        >
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 16,
                display: "grid",
                placeItems: "center",
                margin: "0 auto 14px",
                background: "#111827",
                color: "white",
                fontSize: 24,
                fontWeight: 700,
              }}
            >
              C
            </div>
            <h1 style={{ margin: 0, fontSize: 26 }}>CloudRAG</h1>
            <p style={{ margin: "8px 0 0", color: "#6b7280" }}>
              Document Intelligence
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 8,
              padding: 4,
              background: "#f3f4f6",
              borderRadius: 10,
              marginBottom: 22,
            }}
          >
            {[["login", "Sign in"], ["register", "Create account"]].map(
              ([mode, label]) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => {
                    setAuthMode(mode);
                    setAuthError("");
                  }}
                  style={{
                    border: 0,
                    borderRadius: 8,
                    padding: "10px 8px",
                    background: authMode === mode ? "white" : "transparent",
                    color: authMode === mode ? "#111827" : "#6b7280",
                    fontWeight: 600,
                    cursor: "pointer",
                    boxShadow:
                      authMode === mode
                        ? "0 1px 3px rgba(0,0,0,.08)"
                        : "none",
                  }}
                >
                  {label}
                </button>
              )
            )}
          </div>

          <form onSubmit={handleAuthSubmit}>
            <label style={{ display: "block", marginBottom: 16 }}>
              <span
                style={{
                  display: "block",
                  marginBottom: 7,
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                Email
              </span>
              <input
                type="email"
                value={authEmail}
                onChange={(event) => setAuthEmail(event.target.value)}
                autoComplete="email"
                placeholder="you@example.com"
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  border: "1px solid #d1d5db",
                  borderRadius: 10,
                  padding: "12px 13px",
                  fontSize: 14,
                  outline: "none",
                }}
                required
              />
            </label>

            <label style={{ display: "block", marginBottom: 16 }}>
              <span
                style={{
                  display: "block",
                  marginBottom: 7,
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                Password
              </span>
              <input
                type="password"
                value={authPassword}
                onChange={(event) => setAuthPassword(event.target.value)}
                autoComplete={authMode === "login" ? "current-password" : "new-password"}
                placeholder="At least 8 characters"
                minLength={authMode === "register" ? 8 : 1}
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  border: "1px solid #d1d5db",
                  borderRadius: 10,
                  padding: "12px 13px",
                  fontSize: 14,
                  outline: "none",
                }}
                required
              />
            </label>

            {authError && (
              <div
                style={{
                  marginBottom: 16,
                  padding: "10px 12px",
                  borderRadius: 10,
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b91c1c",
                  fontSize: 13,
                }}
              >
                {authError}
              </div>
            )}

            <button
              type="submit"
              disabled={authSubmitting}
              style={{
                width: "100%",
                border: 0,
                borderRadius: 10,
                padding: "13px 16px",
                background: "#111827",
                color: "white",
                fontWeight: 700,
                cursor: authSubmitting ? "wait" : "pointer",
                opacity: authSubmitting ? 0.7 : 1,
              }}
            >
              {authSubmitting
                ? authMode === "login"
                  ? "Signing in..."
                  : "Creating account..."
                : authMode === "login"
                  ? "Sign in"
                  : "Create account"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main
      className={`app-shell ${
        theme === "dark" ? "theme-dark" : "theme-light"
      }`}
    >
      {mobileSidebarOpen && (
        <button
          type="button"
          className="mobile-sidebar-overlay"
          aria-label="Close menu"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      <aside
        className={`sidebar ${
          mobileSidebarOpen ? "mobile-open" : ""
        }`}
      >
        <div className="sidebar-brand">
          <div className="brand-mark">C</div>

          <div>
            <div className="brand-name">CloudRAG</div>
            <div className="brand-subtitle">
              Document Intelligence
            </div>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={() => createSession()}
          disabled={creatingSession}
        >
          <span className="new-chat-icon">＋</span>
          {creatingSession ? "Creating..." : "New chat"}
        </button>

        <div className="sidebar-section-title">
          Chats
        </div>

        <div className="session-list">
          {loadingSessions && (
            <div className="sidebar-loading">
              Loading chats...
            </div>
          )}

          {!loadingSessions &&
            sessions.length === 0 && (
              <div className="sidebar-empty">
                No conversations yet.
              </div>
            )}

          {sessions.map((session) => (
            <button
              className={`session-item ${
                currentSessionId === session.id
                  ? "active"
                  : ""
              }`}
              key={session.id}
              onClick={() => {
                loadSession(session.id);
                setMobileSidebarOpen(false);
              }}
            >
              <span className="session-icon">▱</span>

              <span className="session-content">
                <span className="session-title">
                  {session.title || "New Chat"}
                </span>

                <span className="session-date">
                  {formatDate(session.updated_at)}
                </span>
              </span>
            </button>
          ))}
        </div>

        <div className="sidebar-bottom">
          <button
            className={`sidebar-tool ${
              knowledgeOpen ? "selected" : ""
            }`}
            onClick={() => {
              setKnowledgeOpen((current) => !current);
              setSystemOpen(false);
              setMobileSidebarOpen(false);
            }}
          >
            <span>▤</span>
            Knowledge base
            <span className="tool-count">
              {documents.length}
            </span>
          </button>

          <button
            className={`sidebar-tool ${
              systemOpen ? "selected" : ""
            }`}
            onClick={() => {
              setSystemOpen((current) => !current);
              setKnowledgeOpen(false);
              setMobileSidebarOpen(false);
            }}
          >
            <span>◉</span>
            System status

            <span
              className={`mini-status ${
                systemHealthy ? "ok" : "bad"
              }`}
            />
          </button>
          <button
            className="sidebar-tool theme-toggle"
            onClick={() =>
              setTheme((current) =>
                current === "dark" ? "light" : "dark"
              )
            }
            title={
              theme === "dark"
                ? "Switch to light mode"
                : "Switch to night mode"
            }
          >
            <span className="theme-toggle-icon">
              {theme === "dark" ? "☀" : "☾"}
            </span>
          
            {theme === "dark"
              ? "Light mode"
              : "Night mode"}

            <span className="theme-switch">
              <span
                className={`theme-switch-knob ${
                  theme === "dark" ? "active" : ""
                }`}
              />
            </span>
          </button>
        </div>
      </aside>

      <section className="chat-shell">
        <header className="chat-header">
          <button
            type="button"
            className="mobile-menu-button"
            aria-label="Open menu"
            onClick={() => setMobileSidebarOpen(true)}
          >
            ☰
          </button>
          <div className="chat-header-left">
            <div className="chat-title">
              {currentSession?.title || "New Chat"}
            </div>

            <div className="chat-subtitle">
              {selectedDocuments.length > 0
                ? `${selectedDocuments.length} document${
                    selectedDocuments.length === 1
                      ? ""
                      : "s"
                  } selected`
                : "Searching all documents"}
            </div>
          </div>

          <div className="chat-header-actions">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginRight: 4,
              }}
            >
              <span
                title={user.email}
                style={{
                  maxWidth: 220,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  fontSize: 13,
                  color: "inherit",
                }}
              >
                {user.email}
              </span>
              <button
                type="button"
                className="icon-button"
                title="Sign out"
                onClick={logout}
              >
                ↪
              </button>
            </div>

            <div
              className={`header-health ${
                systemHealthy ? "healthy" : "degraded"
              }`}
            >
              <span className="health-dot" />

              {systemHealthy
                ? "All systems operational"
                : "System degraded"}
            </div>

            {currentSessionId && (
              <button
                className="icon-button"
                title="Delete conversation"
                onClick={deleteCurrentSession}
                disabled={deletingSession}
              >
                {deletingSession ? "…" : "⌫"}
              </button>
            )}
          </div>
        </header>

        <div className="chat-content">
          <div className="messages-container">
            {loadingMessages ? (
              <div className="chat-loading">
                <div className="loading-spinner" />
                Loading conversation...
              </div>
            ) : sessionMessages.length === 0 ? (
              <div className="welcome-screen">
                <div className="welcome-logo">
                  C
                </div>

                <h1>How can I help with your documents?</h1>

                <p>
                  Ask questions about your uploaded
                  documents. CloudRAG retrieves relevant
                  passages and uses them to generate an
                  answer.
                </p>

                <div className="suggestion-grid">
                  <button
                    onClick={() =>
                      setQuestion(
                        "What are the main topics covered in these documents?"
                      )
                    }
                  >
                    <strong>Summarize</strong>
                    <span>
                      What are the main topics covered?
                    </span>
                  </button>

                  <button
                    onClick={() =>
                      setQuestion(
                        "What are the most important technical details?"
                      )
                    }
                  >
                    <strong>Explore</strong>
                    <span>
                      What are the most important details?
                    </span>
                  </button>

                  <button
                    onClick={() =>
                      setQuestion(
                        "What does the documentation say about monitoring?"
                      )
                    }
                  >
                    <strong>Find information</strong>
                    <span>
                      What does the documentation say about
                      monitoring?
                    </span>
                  </button>

                  <button
                    onClick={() =>
                      setQuestion(
                        "Compare the main approaches described in the documents."
                      )
                    }
                  >
                    <strong>Compare</strong>
                    <span>
                      Compare the approaches described.
                    </span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="message-list">
                {sessionMessages.map((message) => (
                  <article
                    className={`message ${
                      message.role === "user"
                        ? "user-message"
                        : "assistant-message"
                    }`}
                    key={message.id}
                  >
                    <div className="message-avatar">
                      {message.role === "user"
                        ? "You"
                        : "C"}
                    </div>

                    <div className="message-body">
                      <div className="message-role">
                        {message.role === "user"
                          ? "You"
                          : "CloudRAG"}
                      </div>

                      <div className="message-text">
                        {message.content}
                      </div>
                    </div>
                  </article>
                ))}

                {asking && (
                  <article className="message assistant-message">
                    <div className="message-avatar">
                      C
                    </div>

                    <div className="message-body">
                      <div className="message-role">
                        CloudRAG
                      </div>

                      <div className="typing-indicator">
                        <span />
                        <span />
                        <span />
                      </div>
                    </div>
                  </article>
                )}

                {askError && (
                  <div className="chat-error">
                    {askError}
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <div className="composer-area">
            {selectedDocuments.length > 0 && (
              <div className="active-sources">
                <span className="active-sources-label">
                  Using
                </span>

                {selectedDocuments.slice(0, 3).map(
                  (document) => (
                    <span
                      className="source-pill"
                      key={document.id}
                    >
                      {document.filename}
                    </span>
                  )
                )}

                {selectedDocuments.length > 3 && (
                  <span className="source-pill">
                    +{selectedDocuments.length - 3} more
                  </span>
                )}

                <button
                  onClick={() =>
                    setSelectedDocumentIds([])
                  }
                >
                  Clear
                </button>
              </div>
            )}

            <div className="composer">
              <textarea
                ref={textareaRef}
                value={question}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
                onKeyDown={handleComposerKeyDown}
                placeholder="Message CloudRAG..."
                rows={1}
                disabled={asking}
              />

              <button
                className="send-button"
                onClick={askQuestion}
                disabled={
                  asking || !question.trim()
                }
                title="Send message"
              >
                ↑
              </button>
            </div>

            <div className="composer-footer">
              <span>
                CloudRAG answers using your documents
              </span>

              <span>
                Enter to send · Shift + Enter for new line
              </span>
            </div>
          </div>
        </div>
      </section>

      {knowledgeOpen && (
        <aside className="side-panel">
          <div className="side-panel-header">
            <div>
              <h2>Knowledge base</h2>
              <p>
                Manage the documents CloudRAG can use.
              </p>
            </div>

            <button
              className="panel-close"
              onClick={() => setKnowledgeOpen(false)}
            >
              ×
            </button>
          </div>

          <div className="panel-body">
            <div className="upload-box">
              <input
                id="document-upload"
                className="document-file-input"
                type="file"
                accept=".txt,.md,.pdf,.docx,.pptx,.xlsx,.xlsm,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={(event) =>
                  setFile(
                    event.target.files?.[0] || null
                  )
                }
              />

              <label
                htmlFor="document-upload"
                className="file-picker"
              >
                <span className="file-picker-icon">+</span>
              
                <span className="file-picker-content">
                  <strong>
                    {file ? file.name : "Add a document"}
                  </strong>
              
                  <small>
                    {file
                      ? "Ready to upload"
                      : "PDF, DOCX, PPTX, XLSX, TXT or Markdown"}
                  </small>
                </span>
                    
                <span className="file-picker-action">
                  {file ? "Change" : "Browse"}
                </span>
              </label>

              <button
                className="upload-button"
                onClick={uploadDocument}
                disabled={uploading}
              >
                {uploading
                  ? "Uploading..."
                  : "Upload document"}
              </button>

              {uploadStatus && (
                <div className="panel-status">
                  {uploadStatus}
                </div>
              )}
            </div>

            <div className="document-panel-toolbar">
              <label>
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleSelectAll}
                />
                Select all
              </label>

              <span>
                {selectedDocumentIds.length} selected
              </span>
            </div>

            <div className="knowledge-list">
              {loadingDocuments && (
                <div className="panel-empty">
                  Loading documents...
                </div>
              )}

              {!loadingDocuments &&
                documents.length === 0 && (
                  <div className="panel-empty">
                    No documents uploaded yet.
                  </div>
                )}

              {documents.map((document) => {
                const selected =
                  selectedDocumentIds.includes(
                    document.id
                  );

                return (
                  <div
                    className={`knowledge-item ${
                      selected ? "selected" : ""
                    }`}
                    key={document.id}
                  >
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() =>
                        toggleDocument(document.id)
                      }
                    />

                    <div className="knowledge-icon">
                      DOC
                    </div>

                    <div className="knowledge-info">
                      <strong title={document.filename}>
                        {document.filename}
                      </strong>

                      <span>
                        {formatFileSize(
                          document.file_size
                        )}{" "}
                        · {document.status}
                      </span>
                    </div>

                    <button
                      type="button"
                      className="document-download-button"
                      onClick={() =>
                        handleDownloadDocument(document.id)
                      }
                      disabled={document.status !== "completed"}
                      title="Download original document"
                      aria-label={`Download ${document.filename}`}
                    >
                      ↓
                    </button>
                  </div>
                );
              })}
            </div>

            {selectedDocumentIds.length > 0 && (
              <button
                className="delete-documents-button"
                onClick={deleteSelectedDocuments}
                disabled={deletingDocuments}
              >
                {deletingDocuments
                  ? "Deleting..."
                  : `Delete ${selectedDocumentIds.length} selected`}
              </button>
            )}

            <div className="panel-divider" />

            <div className="search-panel">
              <div className="panel-section-title">
                Search documents
              </div>

              <div className="search-input-row">
                <input
                  type="text"
                  value={query}
                  placeholder="Search..."
                  onChange={(event) =>
                    setQuery(event.target.value)
                  }
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      searchDocuments();
                    }
                  }}
                />

                <button
                  onClick={searchDocuments}
                  disabled={
                    searching || !query.trim()
                  }
                >
                  {searching ? "…" : "⌕"}
                </button>
              </div>

              {searchError && (
                <div className="panel-error">
                  {searchError}
                </div>
              )}

              {searchResults.length > 0 && (
                <div className="search-results">
                  {searchResults.map((result) => (
                    <div
                      className="search-result"
                      key={result.chunk_id}
                    >
                      <strong>
                        {result.filename}
                      </strong>

                      <p>{result.content}</p>

                      <span>
                        Chunk {result.chunk_index} ·
                        Distance{" "}
                        {result.distance.toFixed(4)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </aside>
      )}

      {systemOpen && (
        <aside className="side-panel system-panel">
          <div className="side-panel-header">
            <div>
              <h2>System status</h2>
              <p>CloudRAG dependency health.</p>
            </div>

            <button
              className="panel-close"
              onClick={() => setSystemOpen(false)}
            >
              ×
            </button>
          </div>

          <div className="panel-body">
            <div
              className={`overall-status ${
                systemHealthy ? "healthy" : "degraded"
              }`}
            >
              <span className="large-health-dot" />

              <div>
                <strong>
                  {systemHealthy
                    ? "All systems operational"
                    : "System degraded"}
                </strong>

                <span>
                  CloudRAG dependency status
                </span>
              </div>
            </div>

            <div className="dependency-list">
              <div className="dependency">
                <span>API</span>
                <strong className="status-ok">
                  Healthy
                </strong>
              </div>

              <div className="dependency">
                <span>PostgreSQL</span>

                <strong
                  className={
                    health?.dependencies?.database ===
                    "ok"
                      ? "status-ok"
                      : "status-error"
                  }
                >
                  {health?.dependencies?.database ===
                  "ok"
                    ? "Healthy"
                    : "Unavailable"}
                </strong>
              </div>

              <div className="dependency">
                <span>AI Service</span>

                <strong className="status-ok">
                  Connected
                </strong>
              </div>
              </div>

            <div className="health-note">
              Health status automatically refreshes every
              30 seconds.
            </div>
          </div>
        </aside>
      )}
    </main>
  );
}

export default App;