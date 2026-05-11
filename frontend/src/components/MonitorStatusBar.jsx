import { motion } from 'framer-motion'
import { Play, Square, RefreshCw, Radio, Clock, Users } from 'lucide-react'
import toast from 'react-hot-toast'
import { useMonitor } from '../hooks/useMonitor'
import styles from './MonitorStatusBar.module.css'

export default function MonitorStatusBar() {
  const { status, loading, error, fetchStatus, startMonitoring, stopMonitoring } = useMonitor()

  const handleStart = async () => {
    try {
      const res = await startMonitoring()
      toast.success(res.message)
    } catch (e) {
      toast.error(e.message || 'Failed to start monitoring.')
    }
  }

  const handleStop = async () => {
    try {
      const res = await stopMonitoring()
      toast(res.message, { icon: '🛑' })
    } catch (e) {
      toast.error(e.message || 'Failed to stop monitoring.')
    }
  }

  if (loading) {
    return (
      <div className={styles.bar}>
        <div className={styles.loadingDots}>
          <span /><span /><span />
        </div>
        <span className={styles.loadingText}>Connecting to server…</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`${styles.bar} ${styles.barError}`}>
        <span className={styles.statusDot} style={{ background: 'var(--accent-red)' }} />
        <span className={styles.errorText}>Backend offline – {error}</span>
        <button className={styles.iconBtn} onClick={fetchStatus} title="Retry">
          <RefreshCw size={14} />
        </button>
      </div>
    )
  }

  const running = status?.is_monitoring
  const activeCount = status?.active_registrations ?? 0
  const interval = status?.interval_seconds ?? 60

  return (
    <motion.div
      className={`${styles.bar} ${running ? styles.barRunning : styles.barStopped}`}
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Status indicator */}
      <div className={styles.statusLeft}>
        <span className={`${styles.statusDot} ${running ? styles.dotRunning : styles.dotStopped}`} />
        <span className={styles.statusLabel}>
          {running ? 'Monitoring Active' : 'Monitoring Stopped'}
        </span>
      </div>

      {/* Stats */}
      <div className={styles.stats}>
        <span className={styles.stat}>
          <Users size={12} /> {activeCount} watching
        </span>
        <span className={styles.stat}>
          <Clock size={12} /> {interval}s interval
        </span>
      </div>

      {/* Controls */}
      <div className={styles.controls}>
        <button
          className={styles.iconBtn}
          onClick={fetchStatus}
          title="Refresh status"
        >
          <RefreshCw size={14} />
        </button>

        {running ? (
          <button
            className={`${styles.controlBtn} ${styles.controlBtnStop}`}
            onClick={handleStop}
          >
            <Square size={12} fill="currentColor" />
            Stop
          </button>
        ) : (
          <button
            className={`${styles.controlBtn} ${styles.controlBtnStart}`}
            onClick={handleStart}
          >
            <Play size={12} fill="currentColor" />
            Start
          </button>
        )}
      </div>
    </motion.div>
  )
}
