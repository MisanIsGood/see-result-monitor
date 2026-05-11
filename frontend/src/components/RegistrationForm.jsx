import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, Hash, Calendar, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { registrationsApi } from '../utils/api'
import styles from './RegistrationForm.module.css'

const INITIAL = { receiver_email: '', symbol_number: '', date_of_birth: '' }

export default function RegistrationForm({ onSuccess }) {
  const [form, setForm] = useState(INITIAL)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(null)

  const validate = () => {
    const e = {}
    if (!form.receiver_email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/))
      e.receiver_email = 'Enter a valid Gmail address.'
    if (!form.symbol_number.match(/^\d{7,10}$/))
      e.symbol_number = 'Symbol number must be 7–10 digits.'
    if (!form.date_of_birth.match(/^\d{4}[/-]\d{2}[/-]\d{2}$/))
      e.date_of_birth = 'Use format: YYYY/MM/DD (e.g. 2065/05/15)'
    return e
  }

  const onChange = (e) => {
    const { name, value } = e.target
    setForm((p) => ({ ...p, [name]: value }))
    setErrors((p) => ({ ...p, [name]: undefined }))
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) {
      setErrors(errs)
      return
    }

    setLoading(true)
    try {
      const reg = await registrationsApi.create(form)
      setSubmitted(reg)
      toast.success('🎉 Monitoring started! We\'ll email you when your result is published.')
      if (onSuccess) onSuccess(reg)
    } catch (err) {
      if (err.message.includes('already exists') || err.message.includes('409')) {
        toast.error('⚠️ This symbol + email combo is already being monitored.')
      } else {
        toast.error(err.message || 'Failed to register. Is the backend running?')
      }
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setForm(INITIAL)
    setErrors({})
    setSubmitted(null)
  }

  if (submitted) {
    return (
      <motion.div
        className={styles.successCard}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <div className={styles.successIcon}>
          <CheckCircle2 size={48} color="var(--accent-green)" />
        </div>
        <h3 className={styles.successTitle}>You're all set!</h3>
        <p className={styles.successText}>
          We're now watching for SEE result for symbol&nbsp;
          <strong className={styles.mono}>{submitted.symbol_number}</strong>.
          An email will be sent to&nbsp;
          <strong>{submitted.receiver_email}</strong> the moment it's published.
        </p>
        <div className={styles.successMeta}>
          <span>Check count: <strong>0</strong></span>
          <span>Monitoring ID: <strong className={styles.mono}>#{submitted.id}</strong></span>
        </div>
        <button className={styles.btnSecondary} onClick={reset}>
          Register Another
        </button>
      </motion.div>
    )
  }

  return (
    <motion.form
      className={styles.form}
      onSubmit={onSubmit}
      noValidate
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      {/* Email */}
      <div className={styles.field}>
        <label className={styles.label} htmlFor="receiver_email">
          <Mail size={14} className={styles.labelIcon} />
          Receiver Gmail Address
        </label>
        <div className={styles.inputWrap}>
          <input
            id="receiver_email"
            name="receiver_email"
            type="email"
            autoComplete="email"
            placeholder="student@gmail.com"
            value={form.receiver_email}
            onChange={onChange}
            className={`${styles.input} ${errors.receiver_email ? styles.inputError : ''}`}
          />
        </div>
        {errors.receiver_email && (
          <p className={styles.errorMsg}>
            <AlertCircle size={12} /> {errors.receiver_email}
          </p>
        )}
      </div>

      {/* Symbol Number */}
      <div className={styles.field}>
        <label className={styles.label} htmlFor="symbol_number">
          <Hash size={14} className={styles.labelIcon} />
          SEE Symbol Number
        </label>
        <div className={styles.inputWrap}>
          <input
            id="symbol_number"
            name="symbol_number"
            type="text"
            inputMode="numeric"
            placeholder="e.g. 1730XXXX"
            value={form.symbol_number}
            onChange={onChange}
            className={`${styles.input} ${styles.mono} ${errors.symbol_number ? styles.inputError : ''}`}
            maxLength={10}
          />
        </div>
        {errors.symbol_number && (
          <p className={styles.errorMsg}>
            <AlertCircle size={12} /> {errors.symbol_number}
          </p>
        )}
        <p className={styles.hint}>7–10 digit number from your admit card.</p>
      </div>

      {/* Date of Birth */}
      <div className={styles.field}>
        <label className={styles.label} htmlFor="date_of_birth">
          <Calendar size={14} className={styles.labelIcon} />
          Date of Birth
        </label>
        <div className={styles.inputWrap}>
          <input
            id="date_of_birth"
            name="date_of_birth"
            type="text"
            placeholder="YYYY/MM/DD  e.g. 2065/05/15"
            value={form.date_of_birth}
            onChange={onChange}
            className={`${styles.input} ${styles.mono} ${errors.date_of_birth ? styles.inputError : ''}`}
          />
        </div>
        {errors.date_of_birth && (
          <p className={styles.errorMsg}>
            <AlertCircle size={12} /> {errors.date_of_birth}
          </p>
        )}
        <p className={styles.hint}>
          Use Nepali calendar (BS) format: 2065/05/15.
          Must match the DOB on your SEE registration.
        </p>
      </div>

      <button
        type="submit"
        className={styles.btnPrimary}
        disabled={loading}
      >
        {loading ? (
          <>
            <Loader2 size={16} className={styles.spin} />
            Starting Monitoring…
          </>
        ) : (
          '🚀 Start Monitoring'
        )}
      </button>
    </motion.form>
  )
}
