import React from 'react'
import { Folder, Plus, Search, Grid, List } from 'lucide-react'

const ProjectsPage: React.FC = () => {
  const mockProjects = [
    {
      id: 1,
      name: 'Website Redesign',
      description: 'Neugestaltung der Unternehmenswebsite',
      chatCount: 12,
      lastActivity: '2 Stunden',
      color: 'bg-blue-500',
    },
    {
      id: 2,
      name: 'API Documentation',
      description: 'Dokumentation der REST API',
      chatCount: 8,
      lastActivity: '1 Tag',
      color: 'bg-green-500',
    },
    {
      id: 3,
      name: 'Marketing Campaign',
      description: 'Q4 Marketing-Kampagne Planung',
      chatCount: 5,
      lastActivity: '3 Tage',
      color: 'bg-purple-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Folder className="h-8 w-8 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Projekte
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Verwalten Sie Ihre Chat-Projekte und Ordner
              </p>
            </div>
          </div>
          <button className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors">
            <Plus className="h-4 w-4 mr-2" />
            Neues Projekt
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Projekte durchsuchen..."
                className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md">
              <Grid className="h-4 w-4" />
            </button>
            <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md">
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockProjects.map((project) => (
          <div
            key={project.id}
            className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start space-x-3">
              <div className={`w-10 h-10 ${project.color} rounded-lg flex items-center justify-center`}>
                <Folder className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                  {project.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {project.description}
                </p>
              </div>
            </div>
            
            <div className="mt-4 flex items-center justify-between">
              <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                <span>{project.chatCount} Chats</span>
                <span>•</span>
                <span>vor {project.lastActivity}</span>
              </div>
            </div>
          </div>
        ))}

        {/* Create New Project Card */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500 transition-colors cursor-pointer">
          <div className="text-center">
            <Plus className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Neues Projekt
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Erstellen Sie ein neues Projekt für Ihre Chats
            </p>
          </div>
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <Folder className="h-4 w-4 text-white" />
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100">
              Projekt-Management kommt in Phase 3.4
            </h4>
            <p className="text-sm text-blue-700 dark:text-blue-200 mt-1">
              Vollständige Projekt-Verwaltung mit Ordner-Navigation, Drag & Drop und Sharing-Funktionen.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProjectsPage 