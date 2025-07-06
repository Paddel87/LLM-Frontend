import React from 'react'
import { MessageSquare, Bot } from 'lucide-react'

const ChatPage: React.FC = () => {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
        <div className="flex items-center space-x-3">
          <MessageSquare className="h-8 w-8 text-primary-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Chat Interface
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Starten Sie eine Unterhaltung mit Ihrem gewählten LLM
            </p>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 bg-white dark:bg-gray-800 shadow rounded-lg flex flex-col">
        {/* Chat Messages Area */}
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="space-y-4">
            {/* Welcome Message */}
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                  <Bot className="h-5 w-5 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
                  <p className="text-gray-900 dark:text-white">
                    Willkommen beim LLM-Frontend! Ich bin bereit, Ihnen zu helfen. 
                    Stellen Sie mir gerne eine Frage oder beginnen Sie ein Gespräch.
                  </p>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  LLM Assistant • Gerade eben
                </p>
              </div>
            </div>

            {/* Placeholder for future messages */}
            <div className="text-center py-8">
              <div className="text-gray-400 dark:text-gray-600">
                <MessageSquare className="h-12 w-12 mx-auto mb-3" />
                <p className="text-lg font-medium">Keine weiteren Nachrichten</p>
                <p className="text-sm">Beginnen Sie eine Unterhaltung unten</p>
              </div>
            </div>
          </div>
        </div>

        {/* Chat Input */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="flex space-x-3">
            <div className="flex-1">
              <textarea
                rows={1}
                className="w-full resize-none border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-gray-900 dark:text-white bg-white dark:bg-gray-700 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Schreiben Sie Ihre Nachricht hier..."
                disabled
              />
            </div>
            <button
              disabled
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Senden
            </button>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>Chat-Funktionalität kommt in Phase 3.3</span>
            <span>Drücken Sie Enter zum Senden</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage 