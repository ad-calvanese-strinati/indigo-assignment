import { useEffect, useState } from "react";

import { API_BASE_URL, deleteDocument, fetchDocuments, fetchTags, uploadDocument } from "./api";

const emptyForm = {
  file: null,
  tags: "",
};

function formatDate(value) {
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function normalizeTags(rawTags) {
  return rawTags
    .split(",")
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean);
}

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [availableTags, setAvailableTags] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadData() {
    setIsLoading(true);
    setError("");

    try {
      const [documentsResponse, tagsResponse] = await Promise.all([
        fetchDocuments(),
        fetchTags(),
      ]);
      setDocuments(documentsResponse);
      setAvailableTags(tagsResponse.tags);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!form.file) {
      setError("Select a PDF or TXT file before uploading.");
      return;
    }

    setIsSubmitting(true);
    try {
      const tags = normalizeTags(form.tags);
      const result = await uploadDocument({ file: form.file, tags });
      setSuccess(
        result.created
          ? `Uploaded ${result.document.filename} successfully.`
          : `${result.document.filename} was already indexed, so the existing document was reused.`,
      );
      setForm(emptyForm);
      await loadData();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(documentId) {
    setError("");
    setSuccess("");

    try {
      await deleteDocument(documentId);
      setSuccess("Document removed from the knowledge base.");
      await loadData();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  }

  return (
    <div className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Indigo Assignment</p>
          <h1>Knowledge base control room</h1>
          <p className="lede">
            Upload internal documents, assign tags, and keep the MCP knowledge base ready for
            retrieval.
          </p>
        </div>
        <div className="hero-card">
          <span>Backend API</span>
          <strong>{API_BASE_URL}</strong>
        </div>
      </header>

      <main className="layout">
        <section className="panel">
          <div className="panel-heading">
            <h2>Upload document</h2>
            <p>Supported formats: PDF and plain text.</p>
          </div>

          <form className="upload-form" onSubmit={handleSubmit}>
            <label className="field">
              <span>Document file</span>
              <input
                type="file"
                accept=".pdf,.txt,text/plain,application/pdf"
                onChange={(event) =>
                  setForm((current) => ({ ...current, file: event.target.files?.[0] ?? null }))
                }
              />
            </label>

            <label className="field">
              <span>Tags</span>
              <input
                type="text"
                placeholder="compliance, onboarding, product"
                value={form.tags}
                onChange={(event) =>
                  setForm((current) => ({ ...current, tags: event.target.value }))
                }
              />
            </label>

            <button className="primary-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Uploading..." : "Upload to knowledge base"}
            </button>
          </form>

          <div className="tag-bank">
            <div className="panel-heading compact">
              <h3>Known tags</h3>
              <p>Useful to stay consistent during upload.</p>
            </div>
            <div className="tag-list">
              {availableTags.length ? (
                availableTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className="tag-chip"
                    onClick={() =>
                      setForm((current) => {
                        const currentTags = normalizeTags(current.tags);
                        if (currentTags.includes(tag)) {
                          return current;
                        }
                        return {
                          ...current,
                          tags: [...currentTags, tag].join(", "),
                        };
                      })
                    }
                  >
                    {tag}
                  </button>
                ))
              ) : (
                <p className="empty-copy">No tags yet. Upload the first document to create them.</p>
              )}
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Indexed documents</h2>
            <p>Review filenames, tags, upload time, and chunk counts.</p>
          </div>

          {error ? <div className="message error">{error}</div> : null}
          {success ? <div className="message success">{success}</div> : null}

          {isLoading ? (
            <div className="empty-state">Loading documents...</div>
          ) : documents.length ? (
            <div className="document-grid">
              {documents.map((document) => (
                <article className="document-card" key={document.id}>
                  <div className="document-meta">
                    <p className="document-name">{document.filename}</p>
                    <p className="document-date">Uploaded {formatDate(document.upload_date)}</p>
                  </div>

                  <div className="metrics">
                    <div>
                      <span>Chunks</span>
                      <strong>{document.chunk_count}</strong>
                    </div>
                    <div>
                      <span>Type</span>
                      <strong>{document.content_type}</strong>
                    </div>
                  </div>

                  <div className="tag-list">
                    {document.tags.length ? (
                      document.tags.map((tag) => (
                        <span className="tag-chip static" key={`${document.id}-${tag}`}>
                          {tag}
                        </span>
                      ))
                    ) : (
                      <span className="empty-copy">No tags</span>
                    )}
                  </div>

                  <button
                    className="danger-button"
                    type="button"
                    onClick={() => handleDelete(document.id)}
                  >
                    Delete document
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              No documents uploaded yet. Use the form to add the first knowledge source.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
