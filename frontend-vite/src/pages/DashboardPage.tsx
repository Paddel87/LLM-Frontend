import React from 'react'
import { Link } from 'react-router-dom'
import { 
  MessageSquare, 
  Folder, 
  Settings, 
  Plus,
  Clock,
  Zap
} from 'lucide-react'
import { useAuth } from '@/store/auth'

const DashboardPage: React.FC = () => {
  const { user } = useAuth()

  const stats = [
    {
      name: 'Aktive Chats',
      value: '12',
      icon: MessageSquare,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Projekte',
      value: '3',
      icon: Folder,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Tokens verwendet',
      value: '2.4K',
      icon: Zap,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      name: 'Letzte Aktivität',
      value: '2 Min',
      icon: Clock,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ]

  const quickActions = [
    {
      name: 'Neuer Chat',
      description: 'Starte eine neue Unterhaltung',
      href: '/chat',
      icon: MessageSquare,
      color: 'bg-blue-600 hover:bg-blue-700',
    },
    {
      name: 'Neues Projekt',
      description: 'Erstelle ein neues Projekt',
      href: '/projects',
      icon: Folder,
      color: 'bg-green-600 hover:bg-green-700',
    },
    {
      name: 'Einstellungen',
      description: 'Konfiguriere deine Präferenzen',
      href: '/settings',
      icon: Settings,
      color: 'bg-gray-600 hover:bg-gray-700',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Willkommen zurück, {user?.full_name || user?.username}!
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Hier ist eine Übersicht Ihrer Aktivitäten
            </p>
          </div>
          <Link
            to="/chat"
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Neuer Chat
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 rounded-full ${stat.bgColor} flex items-center justify-center`}>
                    <stat.icon className={`h-5 w-5 ${stat.color}`} />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                      {stat.name}
                    </dt>
                    <dd className="text-lg font-medium text-gray-900 dark:text-white">
                      {stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Schnellzugriff
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.href}
              className="group relative rounded-lg p-6 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
            >
              <div>
                <span className={`rounded-lg inline-flex p-3 ${action.color} text-white`}>
                  <action.icon className="h-6 w-6" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {action.name}
                </h3>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {action.description}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Letzte Aktivitäten
        </h2>
        <div className="space-y-3">
          {[
            {
              action: 'Neuer Chat gestartet',
              time: 'vor 2 Minuten',
              icon: MessageSquare,
            },
            {
              action: 'Projekt "Website Redesign" aktualisiert',
              time: 'vor 1 Stunde',
              icon: Folder,
            },
            {
              action: 'Einstellungen geändert',
              time: 'vor 3 Stunden',
              icon: Settings,
            },
          ].map((activity, index) => (
            <div key={index} className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <activity.icon className="h-5 w-5 text-gray-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900 dark:text-white">
                  {activity.action}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {activity.time}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default DashboardPage 