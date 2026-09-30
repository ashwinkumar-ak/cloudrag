import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploading, setUploading] = useState(false);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState([]);
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");

  const [health, setHealth] = useState(null);

  useEffect(() => {
    checkHealth();

    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  async function checkHealth() {
    try {
      const response = await fetch(`${API_URL}/health`);

      if (!response.ok) {
        throw new Error("Health check failed");
      }

      const data = await response.json();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  }

  async function uploadDocument() {
    if (!file) {
      setUploadStatus("Please select a document first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setUploadStatus("");

    try {
      const response = await fetch(`${API_URL}/documents`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setUploadStatus(
        `Uploaded successfully — ${data.filename}`
      );

      setFile(null);

      const fileInput = document.getElementById("document-upload");
      if (fileInput) {
        fileInput.value = "";
      }

      checkHealth();
    } catch (error) {
      setUploadStatus(`Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
    }
  }

  async function searchDocuments() {
    if (!query.trim()) {
      return;
    }

    setSearching(true);
    setSearchError("");

    try {
      const response = await fetch(`${API_URL}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          limit: 5,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Search failed");
      }

      setResults(data);
    } catch (error) {
      setResults([]);
      setSearchError(error.message);
    } finally {
      setSearching(false);
    }
  }

  async function askQuestion() {
    if (!question.trim()) {
      return;
    }

    setAsking(true);
    setAnswer("");
    setCitations([]);
    setAskError("");

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          limit: 3,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Question failed");
      }

      setAnswer(data.answer);
      setCitations(data.citations);
    } catch (error) {
      setAskError(error.message);
    } finally {
      setAsking(false);
    }
  }

  function handleFileChange(event) {
    const selectedFile = event.target.files[0];

    if (!selectedFile) {
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setUploadStatus("");
  }

  const healthOk = health?.status === "ok";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">
            <span className="brand-mark">CR</span>
            <span>CloudRAG</span>
          </div>

          <p className="brand-subtitle">
            Production-style document intelligence
          </p>
        </div>

        <div className={`health-pill ${healthOk ? "healthy" : "degraded"}`}>
          <span className="health-dot" />
          {healthOk ? "All systems operational" : "System degraded"}
        </div>
      </header>

      <main className="dashboard">
        <section className="hero">
          <div>
            <span className="eyebrow">DOCUMENT INTELLIGENCE</span>
            <h1>
              Ask your documents.
              <br />
              Get grounded answers.
            </h1>

            <p>
              Upload documents, search their content semantically, and ask
              CloudRAG questions using retrieved document context.
            </p>
          </div>
        </section>

        <section className="workspace">
          <div className="panel upload-panel">
            <div className="panel-heading">
              <div>
                <span className="step-number">01</span>
                <h2>Upload</h2>
              </div>

              <span className="panel-label">TXT / MD</span>
            </div>

            <p className="panel-description">
              Add a document to the CloudRAG knowledge base.
            </p>

            <label className="file-picker">
              <input
                id="document-upload"
                type="file"
                accept=".txt,.md,text/plain,text/markdown"
                onChange={handleFileChange}
              />

              <span className="file-icon">↑</span>

              <span>
                {file ? (
                  <>
                    <strong>{file.name}</strong>
                    <small>Ready to upload</small>
                  </>
                ) : (
                  <>
                    <strong>Choose a document</strong>
                    <small>Plain text or Markdown</small>
                  </>
                )}
              </span>
            </label>

            <button
              className="primary-button"
              onClick={uploadDocument}
              disabled={uploading || !file}
            >
              {uploading ? "Processing document..." : "Upload document"}
            </button>

            {uploadStatus && (
              <div
                className={`status-message ${
                  uploadStatus.startsWith("Upload failed")
                    ? "error"
                    : "success"
                }`}
              >
                {uploadStatus}
              </div>
            )}
          </div>

          <div className="panel search-panel">
            <div className="panel-heading">
              <div>
                <span className="step-number">02</span>
                <h2>Semantic Search</h2>
              </div>

              <span className="panel-label">VECTOR</span>
            </div>

            <p className="panel-description">
              Find document passages by meaning instead of exact keywords.
            </p>

            <div className="input-row">
              <input
                type="text"
                placeholder="Search your documents..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    searchDocuments();
                  }
                }}
              />

              <button
                className="secondary-button"
                onClick={searchDocuments}
                disabled={searching || !query.trim()}
              >
                {searching ? "Searching..." : "Search"}
              </button>
            </div>

            {searchError && (
              <div className="status-message error">
                {searchError}
              </div>
            )}

            <div className="results">
              {results.length === 0 && !searching && !searchError && (
                <div className="empty-state">
                  <span>⌕</span>
                  <p>Search results will appear here.</p>
                </div>
              )}

              {results.map((result) => (
                <article className="result-card" key={result.chunk_id}>
                  <div className="result-meta">
                    <strong>Document {result.document_id}</strong>
                    <span>
                      Distance {result.distance.toFixed(4)}
                    </span>
                  </div>

                  <p>{result.content}</p>

                  <small>
                    Chunk {result.chunk_index}
                  </small>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="panel ask-panel">
          <div className="panel-heading">
            <div>
              <span className="step-number">03</span>
              <h2>Ask CloudRAG</h2>
            </div>

            <span className="panel-label">RAG</span>
          </div>

          <p className="panel-description">
            Ask a question and receive an answer grounded only in retrieved
            document context.
          </p>

          <div className="ask-input">
            <textarea
              placeholder="What would you like to know about your documents?"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={3}
            />

            <button
              className="primary-button ask-button"
              onClick={askQuestion}
              disabled={asking || !question.trim()}
            >
              {asking ? "Generating answer..." : "Ask CloudRAG"}
            </button>
          </div>

          {asking && (
            <div className="thinking-state">
              <div className="spinner" />
              <div>
                <strong>CloudRAG is thinking</strong>
                <p>
                  Retrieving relevant passages and generating a grounded
                  answer. Local model inference may take a little while.
                </p>
              </div>
            </div>
          )}

          {askError && (
            <div className="status-message error">
              {askError}
            </div>
          )}

          {answer && !asking && (
            <div className="answer-area">
              <div className="answer-header">
                <span className="answer-label">ANSWER</span>
              </div>

              <div className="answer-content">
                {answer}
              </div>

              {citations.length > 0 && (
                <div className="sources">
                  <div className="sources-heading">
                    <span>Sources</span>
                    <small>{citations.length} retrieved</small>
                  </div>

                  <div className="source-list">
                    {citations.map((citation) => (
                      <div className="source-card" key={citation.chunk_id}>
                        <div>
                          <strong>{citation.filename}</strong>
                          <small>
                            Chunk {citation.chunk_index}
                          </small>
                        </div>

                        <span>
                          {citation.distance.toFixed(4)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        <section className="system-panel">
          <div>
            <span className="eyebrow">SYSTEM STATUS</span>
            <h2>Infrastructure health</h2>
          </div>

          <div className="dependency-grid">
            <DependencyStatus
              name="API"
              healthy={healthOk}
            />

            <DependencyStatus
              name="PostgreSQL"
              healthy={health?.dependencies?.database === "ok"}
            />

            <DependencyStatus
              name="Ollama"
              healthy={health?.dependencies?.ollama === "ok"}
            />
          </div>
        </section>
      </main>

      <footer>
        <span>CloudRAG</span>
        <span>Production-style RAG learning project</span>
      </footer>
    </div>
  );
}

function DependencyStatus({ name, healthy }) {
  return (
    <div className="dependency">
      <span className={`dependency-dot ${healthy ? "ok" : "bad"}`} />

      <div>
        <strong>{name}</strong>
        <small>{healthy ? "Healthy" : "Unavailable"}</small>
      </div>
    </div>
  );
}

export default App;