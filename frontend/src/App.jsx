import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import CityPage from './pages/CityPage'
import HealthPage from './pages/HealthPage'
import ChatbotPage from './pages/ChatbotPage'
import DevicesPage from './pages/DevicesPage'
import StatesPage from './pages/StatesPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
        <Navbar />
        <main className="mx-auto max-w-7xl px-4 pb-16 pt-6">
          <Routes>
            <Route path="/"            element={<HomePage    />} />
            <Route path="/city/:name"  element={<CityPage    />} />
            <Route path="/health"      element={<HealthPage  />} />
            <Route path="/chat"        element={<ChatbotPage />} />
            <Route path="/devices"     element={<DevicesPage />} />
            <Route path="/states"      element={<StatesPage  />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
