import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { CheckCircle2, Clock, XCircle, Loader2, Trash2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { registrationsApi } from '../utils/api'
import styles from './RegistrationsPage.module.css'

function StatusBadge({ reg }) {
  if (reg.result_found && reg.email_sent) {
    return <span className={`${styles.badge} ${styles.badgeSuccess}`}><CheckCircle2 size={12} /> Done</span>
  }
  if (reg.result_found) {
    return <span className={`${styles.badge} ${styles.badgeFound}`}><CheckCircle2 size={12} /> Found</span>
  }
  if (reg.is_active) {
    return <span className={`${styles.badge} ${styles.badgeActive}`}><Clock size={12} /> Watching</span>
  }
  return <span className={`${styles.badge} ${styles.badgeCancelled}`}><XCircle size={12} /> Cancelled</span>
}

export default function RegistrationsPage() {
  const [regs, setRegs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = async () => {
    setLoading(true)
    try {
      const data = await registrationsApi.list()
      setRegs(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch() }, [])

  const handleCancel = async (id) => {
    if (!confirm('Cancel monitoring for this registration?')) return
    try {
      await registrationsApi.cancel(id)
      toast.success('Monitoring cancelled.')
      fetch()
    } catch (e) {
      toast.error(e.message)
    }
  }

  return (
    <div>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Registrations</h1>
          <p className={styles.sub}>All active and completed monitoring requests.</p>
        </div>
        <button className={styles.refreshBtn} onClick={fetch} disabled={loading}>
          <RefreshCw size={15} className={loading ? styles.spin : ''} />
          Refresh
        </button>
      </div>

      {loading && regs.length === 0 && (
        <div className={styles.center}>
          <Loader2 size={28} className={styles.spin} color="var(--accent-blue)" />
          <p>Loading…</p>
        </div>
      )}

      {error && (
        <div className={styles.errorBox}>
          ⚠️ {error}
          <button onClick={fetch} className={styles.retryBtn}>Retry</button>
        </div>
      )}

      {!loading && !error && regs.length === 0 && (
        <div className={styles.emptyState}>
          <span style={{ fontSize: 48 }}>📭</span>
          <p>No registrations yet. Go to the home page and add one!</p>
        </div>
      )}

      <div className={styles.list}>
        {regs.map((reg, i) => (
          <motion.div
            key={reg.id}
            className={styles.card}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <div className={styles.cardTop}>
              <div className={styles.symbolWrap}>
                <span className={styles.symbol}>{reg.symbol_number}</span>
                <StatusBadge reg={reg} />
              </div>
              {reg.is_active && !reg.result_found && (
                <button
                  className={styles.cancelBtn}
                  onClick={() => handleCancel(reg.id)}
                  title="Cancel monitoring"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>

            <div className={styles.meta}>
              <span>📧 {reg.receiver_email}</span>
              <span>📅 DOB: {reg.date_of_birth}</span>
              <span>🔍 Checks: {reg.check_count}</span>
              {reg.last_checked_at && (
                <span>🕒 Last: {format(new Date(reg.last_checked_at), 'MMM d, HH:mm')}</span>
              )}
            </div>

            {reg.last_error && (
              <div className={styles.errorChip}>
                ⚠️ {reg.last_error.slice(0, 120)}
              </div>
            )}

            <div className={styles.idRow}>
              Registered: {format(new Date(reg.created_at), 'MMM d, yyyy HH:mm')}
              &nbsp;· ID #{reg.id}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
