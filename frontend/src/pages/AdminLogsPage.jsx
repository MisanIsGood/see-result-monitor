import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { RefreshCw, Loader2 } from 'lucide-react'
import { logsApi } from '../utils/api'
import styles from './AdminLogsPage.module.css'

const EVENT_COLORS = {
  CHECK_STARTED: 'var(--text-muted)',
  RESULT_FOUND:  'var(--accent-green)',
  EMAIL_SENT:    'var(--accent-blue)',
  EMAIL_FAILED:  'var(--accent-amber)',
  NOT_FOUND:     'var(--text-muted)',
  ERROR:         'var(--accent-red)',
}

const EVENT_ICONS = {
  CHECK_STARTED: '🔍',
  RESULT_FOUND:  '✅',
  EMAIL_SENT:    '📧',
  EMAIL_FAILED:  '⚠️',
  NOT_FOUND:     '⏳',
  ERROR:         '❌',
}

export default function AdminLogsPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [error, setError] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(false)

  const fetch = async () => {
    setLoading(true)
    try {
      const data = await logsApi.list({ limit: 200 })
      setLogs(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetch()
  }, [])

  useEffect(() => {
    if (!autoRefresh) return
    const id = setInterval(fetch, 5000)
    return () => clearInterval(id)
  }, [autoRefresh])

  const filtered = filter
    ? logs.filter((l) => l.event_type === filter)
    : logs

  const EVENT_TYPES = ['CHECK_STARTED', 'RESULT_FOUND', 'EMAIL_SENT', 'EMAIL_FAILED', 'NOT_FOUND', 'ERROR']

  return (
    <div>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Admin Logs</h1>
          <p className={styles.sub}>Live monitoring activity — {filtered.length} events shown.</p>
        </div>
        <div className={styles.headerActions}>
          <label className={styles.autoRefreshLabel}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
          <button className={styles.refreshBtn} onClick={fetch} disabled={loading}>
            <RefreshCw size={15} className={loading ? styles.spin : ''} />
          </button>
        </div>
      </div>

      {/* Filter pills */}
      <div className={styles.filters}>
        <button
          className={`${styles.pill} ${filter === '' ? styles.pillActive : ''}`}
          onClick={() => setFilter('')}
        >
          All
        </button>
        {EVENT_TYPES.map((t) => (
          <button
            key={t}
            className={`${styles.pill} ${filter === t ? styles.pillActive : ''}`}
            onClick={() => setFilter(t)}
            style={filter === t ? { borderColor: EVENT_COLORS[t], color: EVENT_COLORS[t] } : {}}
          >
            {EVENT_ICONS[t]} {t.replace('_', ' ')}
          </button>
        ))}
      </div>

      {loading && logs.length === 0 && (
        <div className={styles.center}>
          <Loader2 size={28} className={styles.spin} color="var(--accent-blue)" />
        </div>
      )}

      {error && (
        <div className={styles.errorBox}>⚠️ {error}</div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className={styles.emptyState}>
          <span style={{ fontSize: 40 }}>📋</span>
          <p>No logs yet. Start monitoring to see activity here.</p>
        </div>
      )}

      <div className={styles.logList}>
        {filtered.map((log, i) => (
          <motion.div
            key={log.id}
            className={styles.logRow}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: Math.min(i * 0.02, 0.3) }}
          >
            <span className={styles.logIcon}>{EVENT_ICONS[log.event_type] || '•'}</span>

            <div className={styles.logBody}>
              <div className={styles.logTop}>
                <span
                  className={styles.logType}
                  style={{ color: EVENT_COLORS[log.event_type] || 'var(--text-secondary)' }}
                >
                  {log.event_type}
                </span>
                {log.symbol_number && (
                  <span className={styles.logSymbol}>{log.symbol_number}</span>
                )}
                <span className={styles.logTime}>
                  {format(new Date(log.created_at), 'HH:mm:ss')}
                </span>
              </div>
              <p className={styles.logMsg}>{log.message}</p>
              {log.source_url && (
                <a
                  href={log.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className={styles.logUrl}
                >
                  {log.source_url}
                </a>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
