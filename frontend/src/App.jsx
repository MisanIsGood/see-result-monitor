import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import RegistrationsPage from './pages/RegistrationsPage'
import AdminLogsPage from './pages/AdminLogsPage'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/registrations" element={<RegistrationsPage />} />
        <Route path="/admin/logs" element={<AdminLogsPage />} />
      </Routes>
    </Layout>
  )
}
