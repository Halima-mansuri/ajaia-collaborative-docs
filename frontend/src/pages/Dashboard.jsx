import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import RichTextEditor from '../components/RichTextEditor'
import ShareModal from '../components/ShareModal'

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString()
}

function DocListItem({ doc, active, onClick }) {
  const isOwned = doc.access_type === 'owner'
  return (
    <li className={`doc-item${active ? ' active' : ''}`}>
      <button type="button" className="doc-link" onClick={onClick}>
        <div>{doc.title}</div>
        <div className="doc-meta">
          <span className={`badge ${isOwned ? 'badge-owned' : 'badge-shared'}`}>
            {isOwned ? 'Owned' : 'Shared'}
          </span>
          {!isOwned && doc.access_type === 'view' && (
            <span className="badge badge-view">View only</span>
          )}
          <span>{formatDate(doc.updated_at)}</span>
        </div>
      </button>
    </li>
  )
}

export default function Dashboard() {
  const { user, logout } = useAuth()
  const { docId } = useParams()
  const navigate = useNavigate()
  const importRef = useRef(null)
  const attachRef = useRef(null)

  const [owned, setOwned] = useState([])
  const [shared, setShared] = useState([])
  const [document, setDocument] = useState(null)
  const [accessType, setAccessType] = useState(null)
  const [shares, setShares] = useState([])
  const [attachments, setAttachments] = useState([])
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('<p></p>')
  const [saveStatus, setSaveStatus] = useState('saved')
  const [error, setError] = useState('')
  const [showShare, setShowShare] = useState(false)
  const saveTimer = useRef(null)

  const readOnly = accessType === 'view'

  const loadDocList = useCallback(async () => {
    try {
      const data = await api.listDocuments()
      setOwned(data.owned)
      setShared(data.shared)
    } catch (err) {
      setError(err.message)
    }
  }, [])

  const loadDocument = useCallback(async (id) => {
    if (!id) {
      setDocument(null)
      return
    }
    try {
      const data = await api.getDocument(id)
      setDocument(data.document)
      setAccessType(data.access_type)
      setShares(data.shares)
      setAttachments(data.attachments)
      setTitle(data.document.title)
      setContent(data.document.content)
      setSaveStatus('saved')
      setError('')
    } catch (err) {
      setError(err.message)
      navigate('/')
    }
  }, [navigate])

  useEffect(() => {
    loadDocList()
  }, [loadDocList])

  useEffect(() => {
    loadDocument(docId ? Number(docId) : null)
  }, [docId, loadDocument])

  const scheduleSave = useCallback((newTitle, newContent) => {
    if (!docId || readOnly) return
    setSaveStatus('saving')
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      try {
        await api.updateDocument(Number(docId), { title: newTitle, content: newContent })
        setSaveStatus('saved')
        loadDocList()
      } catch (err) {
        setSaveStatus('error')
        setError(err.message)
      }
    }, 800)
  }, [docId, readOnly, loadDocList])

  const handleTitleChange = (e) => {
    const newTitle = e.target.value
    setTitle(newTitle)
    scheduleSave(newTitle, content)
  }

  const handleContentChange = (html) => {
    setContent(html)
    scheduleSave(title, html)
  }

  const handleNewDoc = async () => {
    try {
      const data = await api.createDocument('Untitled Document', '<p></p>')
      await loadDocList()
      navigate(`/doc/${data.document.id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError('')
    try {
      const data = await api.importDocument(file)
      await loadDocList()
      navigate(`/doc/${data.document.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      e.target.value = ''
    }
  }

  const handleAttach = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !docId) return
    setError('')
    try {
      await api.attachFile(Number(docId), file)
      await loadDocument(Number(docId))
    } catch (err) {
      setError(err.message)
    } finally {
      e.target.value = ''
    }
  }

  const handleDelete = async () => {
    if (!docId || accessType !== 'owner') return
    if (!window.confirm('Delete this document permanently?')) return
    try {
      await api.deleteDocument(Number(docId))
      await loadDocList()
      navigate('/')
    } catch (err) {
      setError(err.message)
    }
  }

  const refreshShares = async () => {
    if (docId) await loadDocument(Number(docId))
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-badge">Ajaia</span>
          Docs
        </div>
        <div className="user-info">
          <span>{user?.name}</span>
          <button type="button" className="btn btn-secondary btn-sm" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <div className="sidebar-actions">
            <button type="button" className="btn btn-primary" onClick={handleNewDoc}>
              + New document
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => importRef.current?.click()}
            >
              Import file
            </button>
            <input
              ref={importRef}
              type="file"
              className="hidden-input"
              accept=".txt,.md,.docx"
              onChange={handleImport}
            />
            <p className="file-hint">Supported: .txt, .md, .docx (max 5 MB)</p>
          </div>

          <h2>My documents</h2>
          <ul className="doc-list">
            {owned.map((d) => (
              <DocListItem
                key={d.id}
                doc={d}
                active={Number(docId) === d.id}
                onClick={() => navigate(`/doc/${d.id}`)}
              />
            ))}
            {owned.length === 0 && <li className="file-hint">No documents yet</li>}
          </ul>

          <h2>Shared with me</h2>
          <ul className="doc-list">
            {shared.map((d) => (
              <DocListItem
                key={d.id}
                doc={d}
                active={Number(docId) === d.id}
                onClick={() => navigate(`/doc/${d.id}`)}
              />
            ))}
            {shared.length === 0 && <li className="file-hint">No shared documents</li>}
          </ul>
        </aside>

        <main className="main-panel">
          {error && (
            <div className="error-banner" style={{ margin: '0.5rem 1.5rem' }}>
              {error}
            </div>
          )}

          {!document ? (
            <div className="empty-state">
              <h2>Welcome, {user?.name}</h2>
              <p>Create a new document or import a file to get started.</p>
            </div>
          ) : (
            <>
              <div className="editor-header">
                <input
                  className="title-input"
                  value={title}
                  onChange={handleTitleChange}
                  disabled={readOnly}
                  placeholder="Document title"
                />
                <span className={`save-status${saveStatus === 'saved' ? ' saved' : ''}`}>
                  {saveStatus === 'saving' && 'Saving…'}
                  {saveStatus === 'saved' && 'Saved'}
                  {saveStatus === 'error' && 'Save failed'}
                </span>
                {accessType === 'owner' && (
                  <>
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowShare(true)}>
                      Share
                    </button>
                    <button type="button" className="btn btn-danger btn-sm" onClick={handleDelete}>
                      Delete
                    </button>
                  </>
                )}
                {!readOnly && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => attachRef.current?.click()}
                  >
                    Attach file
                  </button>
                )}
                <input
                  ref={attachRef}
                  type="file"
                  className="hidden-input"
                  accept=".txt,.md,.docx"
                  onChange={handleAttach}
                />
              </div>

              <RichTextEditor
                content={content}
                onChange={handleContentChange}
                readOnly={readOnly}
              />

              {attachments.length > 0 && (
                <div className="attachments-bar">
                  <strong>Attachments</strong>
                  <ul>
                    {attachments.map((a) => (
                      <li key={a.id}>{a.filename} — uploaded {formatDate(a.uploaded_at)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {showShare && docId && (
        <ShareModal
          docId={Number(docId)}
          shares={shares}
          onClose={() => setShowShare(false)}
          onUpdated={refreshShares}
        />
      )}
    </div>
  )
}
