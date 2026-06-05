import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function ShareModal({ docId, shares, onClose, onUpdated }) {
  const [users, setUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState('')
  const [permission, setPermission] = useState('edit')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.listUsers()
      .then((data) => setUsers(data.users))
      .catch(() => setError('Failed to load users'))
  }, [])

  const sharedIds = new Set(shares.map((s) => s.user_id))
  const availableUsers = users.filter((u) => !sharedIds.has(u.id))

  const handleShare = async (e) => {
    e.preventDefault()
    if (!selectedUser) return
    setLoading(true)
    setError('')
    try {
      await api.shareDocument(docId, Number(selectedUser), permission)
      setSelectedUser('')
      onUpdated()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (userId) => {
    setLoading(true)
    setError('')
    try {
      await api.unshareDocument(docId, userId)
      onUpdated()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Share document</h2>
        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleShare}>
          <div className="form-group">
            <label htmlFor="share-user">Share with</label>
            <select
              id="share-user"
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
            >
              <option value="">Select a user…</option>
              {availableUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.email})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="share-permission">Permission</label>
            <select
              id="share-permission"
              value={permission}
              onChange={(e) => setPermission(e.target.value)}
            >
              <option value="edit">Can edit</option>
              <option value="view">Can view</option>
            </select>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
            <button type="submit" className="btn btn-primary" disabled={!selectedUser || loading}>
              Share
            </button>
          </div>
        </form>

        {shares.length > 0 && (
          <ul className="share-list">
            {shares.map((s) => (
              <li key={s.id}>
                <span>
                  {s.name} — {s.permission === 'edit' ? 'Can edit' : 'View only'}
                </span>
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  onClick={() => handleRemove(s.user_id)}
                  disabled={loading}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
