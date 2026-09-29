import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  async function uploadDocument() {
    if (!file) {
      setUploadStatus("Please select a file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploadStatus("Uploading...");

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
        `Uploaded successfully. Document ID: ${data.document_id}`
      );
    } catch (error) {
      setUploadStatus(`Error: ${error.message}`);
    }
  }

  async function searchDocuments() {
    if (!query.trim()) {
      return;
    }

    setSearching(true);

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
      setResults([
        {
          content: `Error: ${error.message}`,
          distance: 0,
        },
      ]);
    } finally {
      setSearching(false);
    }
  }

  return (
    <main>
      <h1>CloudRAG</h1>
      <p>Document Intelligence & Semantic Search</p>

      <section>
        <h2>Upload Document</h2>

        <input
          type="file"
          accept=".txt,.md,text/plain,text/markdown"
          onChange={(event) => setFile(event.target.files[0])}
        />

        <button onClick={uploadDocument}>
          Upload
        </button>

        {uploadStatus && <p>{uploadStatus}</p>}
      </section>

      <section>
        <h2>Semantic Search</h2>

        <input
          type="text"
          placeholder="Ask something about your documents..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              searchDocuments();
            }
          }}
        />

        <button onClick={searchDocuments} disabled={searching}>
          {searching ? "Searching..." : "Search"}
        </button>

        <div>
          {results.map((result) => (
            <article key={result.chunk_id}>
              <p>{result.content}</p>
              <small>
                Document: {result.document_id} | Similarity distance:{" "}
                {result.distance.toFixed(4)}
              </small>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

export default App;