import React from 'react'
import { Settings, User, Key, Bell, Palette, Globe, Shield } from 'lucide-react'

const SettingsPage: React.FC = () => {
  const settingsSections = [
    {
      title: 'Profil',
      description: 'Verwalten Sie Ihre Profil-Informationen',
      icon: User,
      color: 'bg-blue-500',
      available: true,
    },
    {
      title: 'API-Schlüssel',
      description: 'Konfigurieren Sie Ihre LLM-Provider API-Schlüssel',
      icon: Key,
      color: 'bg-green-500',
      available: false,
    },
    {
      title: 'Benachrichtigungen',
      description: 'E-Mail und Push-Benachrichtigungen',
      icon: Bell,
      color: 'bg-yellow-500',
      available: false,
    },
    {
      title: 'Design & Aussehen',
      description: 'Theme, Schriftart und UI-Präferenzen',
      icon: Palette,
      color: 'bg-purple-500',
      available: true,
    },
    {
      title: 'Sprache & Region',
      description: 'Sprach- und Regionalisierungseinstellungen',
      icon: Globe,
      color: 'bg-indigo-500',
      available: false,
    },
    {
      title: 'Sicherheit & Datenschutz',
      description: 'Passwort, 2FA und Datenschutz-Einstellungen',
      icon: Shield,
      color: 'bg-red-500',
      available: false,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <Settings className="h-8 w-8 text-primary-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Einstellungen
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Konfigurieren Sie Ihre Präferenzen und Einstellungen
            </p>
          </div>
        </div>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {settingsSections.map((section) => (
          <div
            key={section.title}
            className={`bg-white dark:bg-gray-800 shadow rounded-lg p-6 transition-all duration-200 ${
              section.available 
                ? 'hover:shadow-md cursor-pointer border-2 border-transparent hover:border-primary-200 dark:hover:border-primary-700' 
                : 'opacity-75 cursor-not-allowed'
            }`}
          >
            <div className="flex items-start space-x-3">
              <div className={`w-10 h-10 ${section.color} rounded-lg flex items-center justify-center`}>
                <section.icon className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    {section.title}
                  </h3>
                  {!section.available && (
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full">
                      Bald verfügbar
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {section.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Settings */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Schnelleinstellungen
        </h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-900 dark:text-white">
                Dark Mode
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Dunkles Design aktivieren/deaktivieren
              </p>
            </div>
            <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-primary-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
              <span className="translate-x-5 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-900 dark:text-white">
                Automatische Speicherung
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Chats automatisch speichern
              </p>
            </div>
            <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-primary-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
              <span className="translate-x-5 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
            </button>
          </div>

          <div className="flex items-center justify-between opacity-50">
            <div>
              <label className="text-sm font-medium text-gray-900 dark:text-white">
                Desktop-Benachrichtigungen
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Browser-Benachrichtigungen anzeigen
              </p>
            </div>
            <button disabled className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-not-allowed rounded-full border-2 border-transparent bg-gray-200 dark:bg-gray-600 transition-colors duration-200 ease-in-out">
              <span className="translate-x-0 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
            </button>
          </div>
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
              <Settings className="h-4 w-4 text-white" />
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Weitere Einstellungen kommen in Phase 3.2
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              API-Key Management, Benutzerprofile und erweiterte Einstellungen werden implementiert.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage 