import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { 
  Upload, 
  Search, 
  FileText, 
  Trash2, 
  Eye,
  Database,
  Clock,
  Tag,
  AlertCircle,
  CheckCircle,
  Loader2,
  X,
  Plus,
  Filter
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/store/auth'
import toast from 'react-hot-toast'

// Types
interface Document {
  id: string
  title: string
  description?: string
  project_id: number
  chunk_count: number
  created_at: string
  tags: string[]
  status: 'processing' | 'processed' | 'error'
  embedding_model?: string
  embedding_cost?: number
}

interface SearchResult {
  id: string
  content: string
  score: number
  metadata: any
  document_title: string
}

interface SearchResponse {
  results: SearchResult[]
  total: number
  query: string
  processing_time: number
  embedding_cost: number
}

interface UploadResponse {
  id: string
  title: string
  chunk_count: number
  status: string
  embedding_model: string
  embedding_cost: number
}

const KnowledgeBasePage: React.FC = () => {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchMetrics, setSearchMetrics] = useState<{cost: number, time: number} | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedProject, setSelectedProject] = useState<number | null>(null)
  const [filterTags, setFilterTags] = useState<string[]>([])

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    tags: '',
    project_id: 1,
    file: null as File | null
  })

  // Dropzone configuration
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      setUploadForm(prev => ({
        ...prev,
        file,
        title: file.name.split('.')[0]
      }))
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'text/markdown': ['.md'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false
  })

  // API calls
  const uploadDocument = async () => {
    if (!uploadForm.file) {
      toast.error('Bitte wählen Sie eine Datei aus')
      return
    }

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadForm.file)
      formData.append('title', uploadForm.title)
      formData.append('description', uploadForm.description || '')
      formData.append('tags', uploadForm.tags)
      formData.append('project_id', uploadForm.project_id.toString())

      const response = await fetch('/api/v1/rag/documents/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      })

      if (!response.ok) {
        throw new Error('Upload fehlgeschlagen')
      }

      const result: UploadResponse = await response.json()
      
      toast.success(`Dokument "${result.title}" erfolgreich hochgeladen (Kosten: $${result.embedding_cost.toFixed(4)})`)
      setShowUploadModal(false)
      setUploadForm({ title: '', description: '', tags: '', project_id: 1, file: null })
      loadDocuments()
      
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Fehler beim Hochladen des Dokuments')
    } finally {
      setIsUploading(false)
    }
  }

  const loadDocuments = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/rag/documents', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('Laden der Dokumente fehlgeschlagen')
      }

      const data = await response.json()
      setDocuments(data.documents || [])
      
    } catch (error) {
      console.error('Load documents error:', error)
      toast.error('Fehler beim Laden der Dokumente')
    } finally {
      setIsLoading(false)
    }
  }

  const searchDocuments = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }

    setIsSearching(true)
    try {
      const response = await fetch('/api/v1/rag/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          query: searchQuery,
          project_id: selectedProject,
          limit: 10,
          score_threshold: 0.7
        })
      })

      if (!response.ok) {
        throw new Error('Suche fehlgeschlagen')
      }

      const data: SearchResponse = await response.json()
      setSearchResults(data.results || [])
      setSearchMetrics({ 
        cost: data.embedding_cost, 
        time: data.processing_time 
      })
      
    } catch (error) {
      console.error('Search error:', error)
      toast.error('Fehler bei der Suche')
    } finally {
      setIsSearching(false)
    }
  }

  const deleteDocument = async (documentId: string) => {
    if (!window.confirm('Sind Sie sicher, dass Sie dieses Dokument löschen möchten?')) {
      return
    }

    try {
      const response = await fetch(`/api/v1/rag/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('Löschen fehlgeschlagen')
      }

      toast.success('Dokument erfolgreich gelöscht')
      loadDocuments()
      
    } catch (error) {
      console.error('Delete error:', error)
      toast.error('Fehler beim Löschen des Dokuments')
    }
  }

  // Effects
  React.useEffect(() => {
    loadDocuments()
  }, [])

  React.useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (searchQuery.trim()) {
        searchDocuments()
      } else {
        setSearchResults([])
      }
    }, 500)

    return () => clearTimeout(debounceTimer)
  }, [searchQuery, selectedProject])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />
      case 'processed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const filteredDocuments = documents.filter(doc => {
    if (filterTags.length === 0) return true
    return filterTags.some(tag => doc.tags.includes(tag))
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Database className="h-8 w-8 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Knowledge Base
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Verwalten Sie Ihre Dokumente und durchsuchen Sie sie semantisch
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Dokument hochladen
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Semantische Suche in Ihren Dokumenten..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          {isSearching && (
            <LoadingSpinner size="sm" />
          )}
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                Suchergebnisse ({searchResults.length})
              </h3>
              {searchMetrics && (
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span>
                    <Clock className="h-3 w-3 inline mr-1" />
                    {(searchMetrics.time * 1000).toFixed(0)}ms
                  </span>
                  <span>
                    💰 ${searchMetrics.cost.toFixed(6)}
                  </span>
                </div>
              )}
            </div>
            <div className="space-y-2">
              {searchResults.map((result) => (
                <div
                  key={result.id}
                  className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <FileText className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {result.document_title}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500 bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">
                      {(result.score * 100).toFixed(1)}% Match
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                    {result.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Documents Grid */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">
            Dokumente ({filteredDocuments.length})
          </h2>
          <button
            onClick={loadDocuments}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <Clock className="h-4 w-4 mr-1" />
            Aktualisieren
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              Noch keine Dokumente vorhanden
            </p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="mt-2 text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              Erstes Dokument hochladen
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(doc.status)}
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                      {doc.title}
                    </h3>
                  </div>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => setSelectedDocument(doc)}
                      className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deleteDocument(doc.id)}
                      className="p-1 text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {doc.description && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {doc.description}
                  </p>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{doc.chunk_count} Chunks</span>
                  <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                </div>

                {doc.embedding_cost && (
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
                    <span>{doc.embedding_model || 'API'}</span>
                    <span>💰 ${doc.embedding_cost.toFixed(6)}</span>
                  </div>
                )}

                {doc.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {doc.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200"
                      >
                        <Tag className="h-3 w-3 mr-1" />
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Dokument hochladen
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* File Drop Zone */}
              <div
                {...getRootProps()}
                className={cn(
                  'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
                  isDragActive
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
                )}
              >
                <input {...getInputProps()} />
                <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {uploadForm.file ? uploadForm.file.name : 
                    isDragActive ? 'Datei hier ablegen...' : 'Klicken oder Datei hierhin ziehen'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  PDF, TXT, MD, DOC, DOCX (max. 10MB)
                </p>
              </div>

              {/* Form Fields */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Titel
                </label>
                <input
                  type="text"
                  value={uploadForm.title}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Dokumenttitel"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Beschreibung (optional)
                </label>
                <textarea
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={3}
                  placeholder="Kurze Beschreibung des Dokuments"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tags (optional)
                </label>
                <input
                  type="text"
                  value={uploadForm.tags}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, tags: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="tag1, tag2, tag3"
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  Abbrechen
                </button>
                <button
                  onClick={uploadDocument}
                  disabled={!uploadForm.file || isUploading}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
                >
                  {isUploading ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Wird hochgeladen...
                    </>
                  ) : (
                    'Hochladen'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default KnowledgeBasePage 