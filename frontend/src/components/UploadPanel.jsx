import { useState } from 'react'
import { apiClient } from '../utils/api'

export function UploadPanel({ onUploadSuccess }) {
  const [file, setFile] = useState(null)
  const [metadata, setMetadata] = useState({ department: '', category: '' })
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('') // 'success' or 'error'

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setMessage('')
  }

  const handleMetadataChange = (e) => {
    const { name, value } = e.target
    setMetadata(prev => ({ ...prev, [name]: value }))
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file || !metadata.department || !metadata.category) {
      setMessage('Please select file and fill in metadata')
      setMessageType('error')
      return
    }

    setUploading(true)
    setMessage('')

    try {
      const result = await apiClient.ingest(file, metadata)

      const successMsg = `✅ Successfully uploaded: ${file.name}
📚 Created ${result.chunks_created} chunks
💾 File size: ${(result.file_size / 1024).toFixed(2)} KB
📍 Document ID: ${result.document_id}`

      setMessage(successMsg)
      setMessageType('success')
      setFile(null)
      setMetadata({ department: '', category: '' })
      onUploadSuccess?.(result)
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`)
      setMessageType('error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-4">Upload Document</h2>

      <form onSubmit={handleUpload} className="space-y-4">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition">
          <label className="cursor-pointer">
            <input
              type="file"
              accept=".pdf,.md,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="text-gray-600">
              {file ? (
                <div>
                  <div className="text-lg font-medium">{file.name}</div>
                  <div className="text-sm text-gray-500">{(file.size / 1024).toFixed(2)} KB</div>
                </div>
              ) : (
                <div>
                  <div className="text-lg font-medium">Drag & drop or click to upload</div>
                  <div className="text-sm text-gray-500">PDF, Markdown, or text files</div>
                </div>
              )}
            </div>
          </label>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Department
            </label>
            <select
              name="department"
              value={metadata.department}
              onChange={handleMetadataChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select department</option>
              <option value="Platform">Platform</option>
              <option value="DevOps">DevOps</option>
              <option value="Network">Network</option>
              <option value="Security">Security</option>
              <option value="Development">Development</option>
              <option value="Data Analytics">Data Analytics</option>
              <option value="QA/Testing">QA/Testing</option>
              <option value="IT Management">Management</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              name="category"
              value={metadata.category}
              onChange={handleMetadataChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select category</option>
              <option value="Troubleshooting">Troubleshooting</option>
              <option value="Setup">Setup</option>
              <option value="API">API</option>
              <option value="FAQ">FAQ</option>
              <option value="How-to Guide">How-to Guide</option>
              <option value="Glossary">Glossary</option>
              <option value="Migration">Migration</option>
              <option value="Deployment">Deployment</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={uploading || !file}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition"
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </form>

      {message && (
        <div className={`mt-4 p-3 rounded text-sm whitespace-pre-wrap ${
          messageType === 'success'
            ? 'bg-green-50 border border-green-200 text-green-900'
            : 'bg-red-50 border border-red-200 text-red-900'
        }`}>
          {message}
        </div>
      )}
    </div>
  )
}
