import { motion } from 'framer-motion'
import RegistrationForm from '../components/RegistrationForm'
import MonitorStatusBar from '../components/MonitorStatusBar'
import styles from './HomePage.module.css'

const FEATURES = [
  { icon: '🔍', title: 'Multi-Portal Check', desc: 'Checks see.ntc.net.np, result.neb.gov.np, edusanjal & more every 60s.' },
  { icon: '📧', title: 'Instant Email', desc: 'Get a beautiful formatted result email the moment it is published.' },
  { icon: '🔄', title: 'Auto Retry', desc: 'Smart retry logic handles server overloads and temporary failures.' },
  { icon: '🛡️', title: 'No Duplicates', desc: 'Each symbol + email pair is monitored only once.' },
]

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <motion.section
        className={styles.hero}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <div className={styles.heroChip}>
          <span className={styles.chipDot} />
          Nepal SEE 2082 · Automated Monitoring
        </div>

        <h1 className={styles.heroTitle}>
          Never Miss Your<br />
          <span className={styles.heroAccent}>SEE Result</span>
        </h1>

        <p className={styles.heroSub}>
          Enter your details once. We continuously monitor all official SEE portals
          and email you the instant your result is published — no refreshing required.
        </p>
      </motion.section>

      {/* Monitor status */}
      <MonitorStatusBar />

      {/* Form card */}
      <motion.section
        className={styles.card}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.15, ease: 'easeOut' }}
      >
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>Register for Result Alert</h2>
          <p className={styles.cardSub}>
            Fill in your details and we'll notify you via email when your SEE result is out.
          </p>
        </div>
        <RegistrationForm />
      </motion.section>

      {/* How it works */}
      <motion.section
        className={styles.steps}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <h2 className={styles.sectionTitle}>How It Works</h2>
        <div className={styles.stepGrid}>
          {['Enter your Gmail, symbol number & date of birth',
            'Our server starts polling SEE portals every 60 seconds',
            'The moment your result appears, we send you an email',
            'Open the email to see your GPA, grade & subject details'].map((step, i) => (
            <div key={i} className={styles.step}>
              <span className={styles.stepNum}>{i + 1}</span>
              <p className={styles.stepText}>{step}</p>
            </div>
          ))}
        </div>
      </motion.section>

      {/* Features */}
      <motion.section
        className={styles.features}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <h2 className={styles.sectionTitle}>Features</h2>
        <div className={styles.featureGrid}>
          {FEATURES.map(({ icon, title, desc }) => (
            <div key={title} className={styles.featureCard}>
              <span className={styles.featureIcon}>{icon}</span>
              <div>
                <h3 className={styles.featureTitle}>{title}</h3>
                <p className={styles.featureDesc}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.section>

      {/* Disclaimer */}
      <div className={styles.disclaimer}>
        <strong>⚠️ Disclaimer:</strong> This is an unofficial monitoring tool.
        Official results are published on{' '}
        <a href="https://see.ntc.net.np" target="_blank" rel="noreferrer">see.ntc.net.np</a>
        {' '}and{' '}
        <a href="https://result.neb.gov.np" target="_blank" rel="noreferrer">result.neb.gov.np</a>.
      </div>
    </div>
  )
}
