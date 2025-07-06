import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/store/auth'
import { ThemeProvider } from '@/components/providers/ThemeProvider'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

// Pages
import LoginPage from '@/pages/auth/LoginPage.tsx'
import RegisterPage from '@/pages/auth/RegisterPage.tsx'
import DashboardPage from '@/pages/DashboardPage.tsx'
import ChatPage from '@/pages/ChatPage.tsx'
import ProjectsPage from '@/pages/ProjectsPage.tsx'
import SettingsPage from '@/pages/SettingsPage.tsx'
import KnowledgeBasePage from '@/pages/KnowledgeBasePage.tsx'
import NotFoundPage from '@/pages/NotFoundPage.tsx'

// Layout Components
import ProtectedRoute from '@/components/auth/ProtectedRoute.tsx'
import MainLayout from '@/components/layout/MainLayout.tsx'

function App() {
  const { isAuthenticated, isLoading, refreshUser } = useAuth()

  useEffect(() => {
    // Beim Start der App prüfen, ob der User noch authentifiziert ist
    if (!isAuthenticated && !isLoading) {
      refreshUser()
    }
  }, [isAuthenticated, isLoading, refreshUser])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Routes>
          {/* Public Routes */}
          <Route 
            path="/login" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
            } 
          />
          <Route 
            path="/register" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />
            } 
          />

          {/* Protected Routes */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="chat/:chatId?" element={<ChatPage />} />
            <Route path="knowledge" element={<KnowledgeBasePage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </ThemeProvider>
  )
}

export default App 