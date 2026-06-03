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
    <div className="bg-white border-b border-gray-200 p-4">
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-40">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Department
          </label>
          <select
            name="department"
            value={filters.department}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All departments</option>
            <option value="Platform">Platform</option>
            <option value="DevOps">DevOps</option>
            <option value="Network">Network</option>
            <option value="Security">Security</option>
          </select>
        </div>

        <div className="flex-1 min-w-40">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <select
            name="category"
            value={filters.category}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All categories</option>
            <option value="Troubleshooting">Troubleshooting</option>
            <option value="Setup">Setup</option>
            <option value="API">API</option>
            <option value="FAQ">FAQ</option>
          </select>
        </div>

        <div className="flex-1 min-w-40">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            From
          </label>
          <input
            type="date"
            name="dateFrom"
            value={filters.dateFrom}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex-1 min-w-40">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            To
          </label>
          <input
            type="date"
            name="dateTo"
            value={filters.dateTo}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  )
}
