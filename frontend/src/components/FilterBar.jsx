import { useState } from 'react'

export function FilterBar({ onFilterChange }) {
  const [filters, setFilters] = useState({
    department: '',
    category: '',
    dateFrom: '',
    dateTo: ''
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    const newFilters = { ...filters, [name]: value }
    setFilters(newFilters)
    onFilterChange?.(newFilters)
  }

  return (
    <div className="bg-gradient-to-r from-white to-blue-50 dark:from-gray-800 dark:to-gray-900 border-b-2 border-blue-200 dark:border-blue-800 p-6 shadow-md">
      <div className="flex gap-5 flex-wrap items-end">
        <div className="flex-1 min-w-48">
          <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wider">
            🏢 Department
          </label>
          <select
            name="department"
            value={filters.department}
            onChange={handleChange}
            className="w-full px-4 py-2.5 border-2 border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white transition-all duration-300 hover:border-blue-400"
          >
            <option value="">All departments</option>
            <option value="Platform">Platform</option>
            <option value="DevOps">DevOps</option>
            <option value="Network">Network</option>
            <option value="Security">Security</option>
          </select>
        </div>

        <div className="flex-1 min-w-48">
          <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wider">
            📂 Category
          </label>
          <select
            name="category"
            value={filters.category}
            onChange={handleChange}
            className="w-full px-4 py-2.5 border-2 border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white transition-all duration-300 hover:border-blue-400"
          >
            <option value="">All categories</option>
            <option value="Troubleshooting">Troubleshooting</option>
            <option value="Setup">Setup</option>
            <option value="API">API</option>
            <option value="FAQ">FAQ</option>
          </select>
        </div>

        <div className="flex-1 min-w-48">
          <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wider">
            📅 From Date
          </label>
          <input
            type="date"
            name="dateFrom"
            value={filters.dateFrom}
            onChange={handleChange}
            className="w-full px-4 py-2.5 border-2 border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white transition-all duration-300 hover:border-blue-400"
          />
        </div>

        <div className="flex-1 min-w-48">
          <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wider">
            📅 To Date
          </label>
          <input
            type="date"
            name="dateTo"
            value={filters.dateTo}
            onChange={handleChange}
            className="w-full px-4 py-2.5 border-2 border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white transition-all duration-300 hover:border-blue-400"
          />
        </div>
      </div>
    </div>
  )
}
