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
  getModels,
  updateSessionModel,
  streamAskQuestion,
  downloadDocument,
  fetchDocumentImagePreview,
  reindexMultimodalImages,
  compareDocuments,
  runEvaluation,
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
const [selectedCitation, setSelectedCitation] = useState(null);
const [citationImageUrl, setCitationImageUrl] = useState("");
const [citationImageLoading, setCitationImageLoading] = useState(false);
const [systemOpen, setSystemOpen] = useState(false);
  const [evaluationOpen, setEvaluationOpen] = useState(false);
  const [evaluationCases, setEvaluationCases] = useState(
    JSON.stringify(
      [
        {
          question: "What is the main topic of this document?",
          expected_answer: "Replace this with the reference answer.",
          expected_document_ids: [],
          document_ids: [],
          limit: 5,
        },
      ],
      null,
      2
    )
  );
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [evaluationError, setEvaluationError] = useState("");
const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
const [comparisonOpen, setComparisonOpen] = useState(false);
const [comparisonLoading, setComparisonLoading] = useState(false);
const [comparisonResult, setComparisonResult] = useState(null);
const [comparisonError, setComparisonError] = useState("");

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [reindexingImages, setReindexingImages] = useState(false);
  const [reindexMessage, setReindexMessage] = useState("");

  const [health, setHealth] = useState(null);
  const [models, setModels] = useState([]);
  const [modelChanging, setModelChanging] = useState(false);
  const [modelError, setModelError] = useState("");

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
  setSelectedCitation(null);

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

async function loadModels() {
  try {
    const data = await getModels();
    setModels(data.models || []);
  } catch (error) {
    console.error(error);
    setModels([]);
  }
}

async function handleModelChange(event) {
  const model = event.target.value;

  if (!currentSessionId || !model || modelChanging) {
    return;
  }

  setModelChanging(true);
  setModelError("");

  try {
    const updated = await updateSessionModel(currentSessionId, model);

    setSessions((current) =>
      current.map((session) =>
        session.id === updated.id ? updated : session
      )
    );
  } catch (error) {
    setModelError(error.message || "Could not change model.");
  } finally {
    setModelChanging(false);
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
      `${data.filename} queued for processing.`
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


  async function retryDocument(documentId) {
    try {
      await apiFetch(`/documents/${documentId}/retry`, {
        method: "POST",
      });
      await loadDocuments();
    } catch (error) {
      window.alert(`Retry failed: ${error.message}`);
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

async function reindexVisualSearch() {
  setReindexingImages(true);
  setReindexMessage("");
  try {
    const data = await reindexMultimodalImages();
    setReindexMessage(
      `Visual index updated: ${data.embedded} image(s) embedded${data.skipped ? `, ${data.skipped} skipped` : ""}.`
    );
  } catch (error) {
    setReindexMessage(`Visual index update failed: ${error.message}`);
  } finally {
    setReindexingImages(false);
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

useEffect(() => {
  let objectUrl = "";

  async function loadCitationImage() {
    const image = selectedCitation?.image_evidence?.[0];
    setCitationImageUrl("");

    if (!image?.image_id) {
      setCitationImageLoading(false);
      return;
    }

    setCitationImageLoading(true);
    try {
      const blob = await fetchDocumentImagePreview(image.image_id);
      objectUrl = URL.createObjectURL(blob);
      setCitationImageUrl(objectUrl);
    } catch (error) {
      setCitationImageUrl("");
      setAskError(error.message);
    } finally {
      setCitationImageLoading(false);
    }
  }

  loadCitationImage();

  return () => {
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
    }
  };
}, [selectedCitation]);

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

  const temporaryAssistantMessage = {
    id: `temp-assistant-${Date.now()}`,
    role: "assistant",
    content: "",
    citations: [],
    created_at: new Date().toISOString(),
    temporary: true,
    streaming: true,
  };

  setSessionMessages((current) => [
    ...current,
    temporaryUserMessage,
    temporaryAssistantMessage,
  ]);

  setQuestion("");
  setAskError("");
  setAsking(true);

  try {
    let streamedSessionId = sessionId;
    let streamedCitations = [];

    await streamAskQuestion(
      trimmedQuestion,
      3,
      selectedDocumentIds,
      sessionId,
      (eventName, data) => {
        if (eventName === "meta") {
          streamedSessionId = data.session_id || streamedSessionId;
          streamedCitations = data.citations || [];

          setCurrentSessionId(streamedSessionId);

          setSessionMessages((current) =>
            current.map((message) =>
              message.id === temporaryAssistantMessage.id
                ? {
                    ...message,
                    citations: streamedCitations,
                  }
                : message
            )
          );
          return;
        }

        if (eventName === "token") {
          setSessionMessages((current) =>
            current.map((message) =>
              message.id === temporaryAssistantMessage.id
                ? {
                    ...message,
                    content: `${message.content || ""}${data.text || ""}`,
                  }
                : message
            )
          );
          return;
        }

        if (eventName === "error") {
          throw new Error(
            data.detail || "The streamed response failed."
          );
        }
      }
    );

    setSessionMessages((current) =>
      current.map((message) =>
        message.id === temporaryAssistantMessage.id
          ? { ...message, streaming: false, temporary: false }
          : message.id === temporaryUserMessage.id
            ? { ...message, temporary: false }
            : message
      )
    );

    // Keep the streamed UI in place. The complete assistant response has
    // already been persisted by the streaming endpoint, so reloading the
    // entire session here would briefly replace the chat with the loading
    // state and make the page appear to refresh.
    setCurrentSessionId(streamedSessionId);
    await refreshSessionList(streamedSessionId);
  } catch (error) {
    setSessionMessages((current) =>
      current.filter(
        (message) =>
          message.id !== temporaryUserMessage.id &&
          message.id !== temporaryAssistantMessage.id
      )
    );

    setAskError(error.message);
  } finally {
    setAsking(false);
  }
}

 async function runRAGEvaluation() {
  if (evaluationLoading) {
    return;
  }

  setEvaluationLoading(true);
  setEvaluationError("");
  setEvaluationResult(null);

  try {
    let parsedCases;

    try {
      parsedCases = JSON.parse(evaluationCases);
    } catch {
      throw new Error("Evaluation cases must contain valid JSON.");
    }

    if (!Array.isArray(parsedCases)) {
      throw new Error("Evaluation cases must be a JSON array.");
    }

    if (parsedCases.length < 1 || parsedCases.length > 10) {
      throw new Error("Provide between 1 and 10 evaluation cases.");
    }

    for (const [index, item] of parsedCases.entries()) {
      if (!item || typeof item !== "object") {
        throw new Error(`Case ${index + 1} must be a JSON object.`);
      }

      if (!String(item.question || "").trim()) {
        throw new Error(`Case ${index + 1} is missing a question.`);
      }

      if (!String(item.expected_answer || "").trim()) {
        throw new Error(`Case ${index + 1} is missing expected_answer.`);
      }
    }

    const result = await runEvaluation(parsedCases, 5);
    setEvaluationResult(result);
  } catch (error) {
    setEvaluationError(error.message || "Evaluation failed.");
  } finally {
    setEvaluationLoading(false);
  }
}

 async function runDocumentComparison() {
  if (selectedDocumentIds.length !== 2 || comparisonLoading) {
    return;
  }

  setComparisonOpen(true);
  setComparisonLoading(true);
  setComparisonResult(null);
  setComparisonError("");

  try {
    const result = await compareDocuments(selectedDocumentIds);
    setComparisonResult(result);
  } catch (error) {
    setComparisonError(error.message);
  } finally {
    setComparisonLoading(false);
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
    loadModels();
    loadDocuments();
    loadHealth();

    const interval = setInterval(loadHealth, 30000);

    return () => clearInterval(interval);
  }, [user]);

  useEffect(() => {
    if (!user) {
      return undefined;
    }

    const hasProcessingDocuments = documents.some(
      (document) =>
        document.status === "pending" ||
        document.status === "processing"
    );

    if (!hasProcessingDocuments) {
      return undefined;
    }

    const interval = setInterval(loadDocuments, 2000);

    return () => clearInterval(interval);
  }, [user, documents]);


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
          <img
            className="auth-brand-mark"
            src="/icon-192.png"
            alt="CloudRAG"
          />
          <strong style={{ fontSize: 18 }}>CloudRAG</strong>
          <div style={{ marginTop: 8, color: "#6b7280" }}>Loading...</div>
        </div>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <div className="auth-header">
            <img
              className="auth-brand-mark"
              src="/icon-192.png"
              alt="CloudRAG"
            />
            <h1 className="auth-title">CloudRAG</h1>
            <p className="auth-subtitle">Document Intelligence</p>
          </div>

          <div className="auth-mode-switch">
            {[['login', 'Sign in'], ['register', 'Create account']].map(
              ([mode, label]) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => {
                    setAuthMode(mode);
                    setAuthError("");
                  }}
                  className={`auth-mode-button ${
                    authMode === mode ? "active" : ""
                  }`}
                >
                  {label}
                </button>
              )
            )}
          </div>

          <form onSubmit={handleAuthSubmit} className="auth-form">
            <label className="auth-field">
              <span className="auth-label">Email</span>
              <input
                type="email"
                value={authEmail}
                onChange={(event) => setAuthEmail(event.target.value)}
                autoComplete="email"
                placeholder="you@example.com"
                className="auth-input"
                required
              />
            </label>

            <label className="auth-field">
              <span className="auth-label">Password</span>
              <input
                type="password"
                value={authPassword}
                onChange={(event) => setAuthPassword(event.target.value)}
                autoComplete={authMode === "login" ? "current-password" : "new-password"}
                placeholder="At least 8 characters"
                minLength={authMode === "register" ? 8 : 1}
                className="auth-input"
                required
              />
            </label>

            {authError && (
              <div className="auth-error">
                {authError}
              </div>
            )}

            <button
              type="submit"
              disabled={authSubmitting}
              className="auth-submit"
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
          <img
            className="brand-mark"
            src="/icon-192.png"
            alt="CloudRAG"
          />

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
              evaluationOpen ? "selected" : ""
            }`}
            onClick={() => {
              setEvaluationOpen((current) => !current);
              setKnowledgeOpen(false);
              setSystemOpen(false);
              setMobileSidebarOpen(false);
            }}
          >
            <span>◈</span>
            Evaluation
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
            {currentSession && models.length > 0 && (
              <label className="model-selector" title={modelError || "Choose the model used for this chat"}>
                <span>Model</span>
                <select
                  value={currentSession.model || ""}
                  onChange={handleModelChange}
                  disabled={modelChanging}
                  aria-label="Select AI model"
                >
                  {models.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
                {modelChanging && <span className="model-selector-status">Saving…</span>}
              </label>
            )}

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
                        {message.streaming && (
                          <span className="streaming-cursor" />
                        )}
                      </div>

                      {message.role === "assistant" &&
                        message.citations?.length > 0 && (
                          <div className="message-citations">
                            <div className="message-citations-label">
                              Sources
                            </div>

                            <div className="message-citation-list">
                              {message.citations.map(
                                (citation, index) => (
                                  <button
                                    type="button"
                                    className="citation-button"
                                    key={`${message.id}-${citation.chunk_id}`}
                                    onClick={() =>
                                      setSelectedCitation({
                                        ...citation,
                                        number: index + 1,
                                      })
                                    }
                                    title={`View source ${index + 1}: ${citation.filename}`}
                                  >
                                    <span className="citation-number">
                                      {index + 1}
                                    </span>
                                    <span className="citation-filename">
                                      {citation.filename}
                                    </span>
                                    <span className="citation-arrow">
                                      →
                                    </span>
                                  </button>
                                )
                              )}
                            </div>
                          </div>
                        )}
                    </div>
                  </article>
                ))}

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

      {comparisonOpen && (
        <div className="comparison-overlay" onClick={() => setComparisonOpen(false)}>
          <section className="comparison-panel" onClick={(event) => event.stopPropagation()}>
            <div className="comparison-header">
              <div>
                <h2>Document comparison</h2>
                <p>Evidence-based comparison of the two selected documents.</p>
              </div>
              <button
                type="button"
                className="panel-close"
                onClick={() => setComparisonOpen(false)}
              >
                ×
              </button>
            </div>

            <div className="comparison-body">
              {comparisonLoading && (
                <div className="comparison-loading">
                  <div className="loading-spinner" />
                  Comparing the selected documents...
                </div>
              )}

              {comparisonError && (
                <div className="panel-error">{comparisonError}</div>
              )}

              {comparisonResult && (
                <>
                  <div className="comparison-documents">
                    {comparisonResult.documents.map((document) => (
                      <div className="comparison-document" key={document.id}>
                        <span>Document</span>
                        <strong title={document.filename}>{document.filename}</strong>
                      </div>
                    ))}
                  </div>

                  <div className="comparison-answer">
                    {comparisonResult.answer}
                  </div>

                  {comparisonResult.citations?.length > 0 && (
                    <div className="comparison-sources">
                      <h3>Evidence used</h3>
                      {comparisonResult.citations.map((citation, index) => (
                        <button
                          type="button"
                          className="comparison-source"
                          key={`${citation.document_id}-${citation.chunk_id}`}
                          onClick={() => setSelectedCitation({ ...citation, number: index + 1 })}
                        >
                          <span>{index + 1}</span>
                          <strong>{citation.filename}</strong>
                          <small>Chunk {citation.chunk_index}</small>
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </section>
        </div>
      )}

      {selectedCitation && (
        <>
          <button
            type="button"
            className="citation-panel-overlay"
            aria-label="Close citation"
            onClick={() => setSelectedCitation(null)}
          />

          <aside className="citation-panel">
            <div className="side-panel-header">
              <div>
                <h2>Source {selectedCitation.number}</h2>
                <p>Retrieved document evidence.</p>
              </div>

              <button
                className="panel-close"
                onClick={() => setSelectedCitation(null)}
                aria-label="Close citation"
              >
                ×
              </button>
            </div>

            <div className="panel-body citation-panel-body">
              <div className="citation-source-card">
                <strong>{selectedCitation.filename}</strong>
                <span>
                  Chunk {selectedCitation.chunk_index}
                </span>
              </div>

              {selectedCitation.image_evidence?.length > 0 && (
                <div className="citation-visual-evidence">
                  <div className="citation-evidence-label">
                    Visual evidence
                  </div>

                  {citationImageLoading && (
                    <div className="citation-image-loading">Loading image preview…</div>
                  )}

                  {citationImageUrl && (
                    <figure className="citation-image-figure">
                      <img
                        src={citationImageUrl}
                        alt={
                          selectedCitation.image_evidence[0].source_label ||
                          "Source visual evidence"
                        }
                        className="citation-image-preview"
                      />
                      <figcaption>
                        {selectedCitation.image_evidence[0].source_label ||
                          `Image ${selectedCitation.image_evidence[0].image_index}`}
                      </figcaption>
                    </figure>
                  )}
                </div>
              )}

              <div className="citation-evidence-label">
                Source evidence
              </div>

              <blockquote className="citation-evidence">
                {selectedCitation.content}
              </blockquote>

              <div className="citation-meta">
                Retrieval distance: {
                  Number(selectedCitation.distance).toFixed(4)
                }
              </div>

              <button
                type="button"
                className="citation-download-button"
                onClick={async () => {
                  try {
                    await downloadDocument(
                      selectedCitation.document_id
                    );
                  } catch (error) {
                    setAskError(error.message);
                  }
                }}
              >
                Download original document
              </button>
            </div>
          </aside>
        </>
      )}

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
            <div className="multimodal-index-tools">
              <button
                type="button"
                className="secondary-action-button"
                onClick={reindexVisualSearch}
                disabled={reindexingImages}
              >
                {reindexingImages ? "Building visual index…" : "Build visual search index"}
              </button>
              {reindexMessage && <div className="reindex-message">{reindexMessage}</div>}
            </div>

            <div className="upload-box">
              <input
                id="document-upload"
                className="document-file-input"
                type="file"
                accept=".txt,.md,.pdf,.docx,.pptx,.xlsx,.xlsm,.csv,.jpg,.jpeg,.png,.webp,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,image/jpeg,image/png,image/webp"
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
                      ? "Ready to upload (documents, spreadsheets, or images)"
                      : "PDF, DOCX, PPTX, XLSX, images, TXT or Markdown"}
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

              <button
                type="button"
                className="compare-button"
                onClick={runDocumentComparison}
                disabled={selectedDocumentIds.length !== 2 || comparisonLoading}
                title="Select exactly two completed documents to compare"
              >
                {comparisonLoading ? "Comparing..." : "Compare"}
              </button>
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
                      <span className="document-id">
                        Document ID: {document.id}
                      </span>

                      <span>
                        {formatFileSize(
                          document.file_size
                        )}{" "}
                        · {document.status}
                        {document.processing_stage &&
                          document.status !== "completed" &&
                          ` · ${document.processing_stage}`}
                      </span>

                      {(document.status === "pending" ||
                        document.status === "processing") && (
                        <div className="document-progress">
                          <div className="document-progress-track">
                            <div
                              className="document-progress-bar"
                              style={{
                                width: `${document.processing_progress || 0}%`,
                              }}
                            />
                          </div>
                          <small>
                            {document.processing_progress || 0}%
                          </small>
                        </div>
                      )}

                      {document.status === "failed" && (
                        <div className="document-error">
                          <small title={document.error_message || "Processing failed."}>
                            {document.error_message || "Processing failed."}
                          </small>
                          <button
                            type="button"
                            className="document-retry-button"
                            onClick={() => retryDocument(document.id)}
                          >
                            Retry
                          </button>
                        </div>
                      )}
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
                      className={`search-result ${result.result_type === "image" ? "search-result-image" : ""}`}
                      key={`${result.result_type}-${result.chunk_id}`}
                    >
                      <div className="search-result-header">
                        <strong>{result.filename}</strong>
                        {result.result_type === "image" && (
                          <span className="search-result-type">Visual match</span>
                        )}
                      </div>

                      <p>{result.content}</p>

                      <span>
                        {result.result_type === "image"
                          ? `${result.image_source_label || "Image"} · `
                          : `Chunk ${result.chunk_index} · `}
                        Distance {result.distance.toFixed(4)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </aside>
      )}

      {evaluationOpen && (
        <aside className="side-panel evaluation-panel">
          <div className="side-panel-header">
            <div>
              <h2>RAG evaluation</h2>
              <p>Measure retrieval and answer quality against reference cases.</p>
            </div>
            <button
              className="panel-close"
              onClick={() => setEvaluationOpen(false)}
            >
              ×
            </button>
          </div>

          <div className="panel-body">
            <div className="evaluation-note">
              Add up to 10 cases. Each case can optionally specify the document IDs
              that should be retrieved. Evaluation runs against your private documents.
            </div>

            <div className="panel-section-title">Evaluation cases (JSON)</div>
            <textarea
              className="evaluation-textarea"
              value={evaluationCases}
              onChange={(event) => setEvaluationCases(event.target.value)}
              spellCheck="false"
            />

            <button
              type="button"
              className="upload-button evaluation-run-button"
              onClick={runRAGEvaluation}
              disabled={evaluationLoading}
            >
              {evaluationLoading ? "Running evaluation..." : "Run evaluation"}
            </button>

            {evaluationError && (
              <div className="panel-error">{evaluationError}</div>
            )}

            {evaluationResult && (
              <div className="evaluation-results">
                <div className="evaluation-metrics">
                  <div className="evaluation-metric">
                    <span>Retrieval hit rate</span>
                    <strong>
                      {evaluationResult.retrieval_hit_rate == null
                        ? "N/A"
                        : `${(evaluationResult.retrieval_hit_rate * 100).toFixed(1)}%`}
                    </strong>
                  </div>
                  <div className="evaluation-metric">
                    <span>Answer coverage</span>
                    <strong>{(evaluationResult.reference_answer_coverage * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="evaluation-metric">
                    <span>Exact match</span>
                    <strong>{(evaluationResult.exact_match_rate * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="evaluation-metric">
                    <span>Average latency</span>
                    <strong>{evaluationResult.average_latency_ms} ms</strong>
                  </div>
                  <div className="evaluation-metric">
                    <span>P95 latency</span>
                    <strong>{evaluationResult.p95_latency_ms} ms</strong>
                  </div>
                  <div className="evaluation-metric">
                    <span>Cases</span>
                    <strong>{evaluationResult.successful_cases}/{evaluationResult.cases}</strong>
                  </div>
                </div>

                <div className="panel-section-title">Case results</div>
                {evaluationResult.results.map((item) => (
                  <div className="evaluation-case" key={item.case_number}>
                    <div className="evaluation-case-header">
                      <strong>Case {item.case_number}</strong>
                      <span>{item.latency_ms} ms</span>
                    </div>
                    <p>{item.question}</p>
                    <div className="evaluation-case-status">
                      Retrieval: {item.retrieval_hit ? "Hit" : "Miss"} · Coverage: {(item.answer_coverage * 100).toFixed(1)}% · Exact: {item.exact_match ? "Yes" : "No"}
                    </div>
                    {item.error ? (
                      <div className="document-error"><small>{item.error}</small></div>
                    ) : (
                      <details>
                        <summary>Generated answer</summary>
                        <div className="evaluation-answer">{item.generated_answer}</div>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
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