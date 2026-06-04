import { useState } from 'react'
import { Lock, Copy, Eye, EyeOff, AlertCircle, User, Mail, Building2 } from 'lucide-react'

export function AuthModal({
  onLogin,
  onRegister,
  darkMode = true,
  loginError = '',
  registrationError = '',
  isLoggingIn = false,
  isRegistering = false
}) {
  const [showTab, setShowTab] = useState('login') // 'login' or 'register'
  const [showPassword, setShowPassword] = useState(false)
  const [showRegPassword, setShowRegPassword] = useState(false)
  const [copied, setCopied] = useState(false)

  // Login form
  const [apiKey, setApiKey] = useState('')
  const [loginUsername, setLoginUsername] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginMethod, setLoginMethod] = useState('api') // 'api' or 'password'

  // Registration form
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [department, setDepartment] = useState('')

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`h-screen flex items-center justify-center ${darkMode ? 'dark' : ''} bg-gradient-to-br from-blue-600 via-blue-700 to-purple-800 dark:from-blue-900 dark:via-purple-900 dark:to-slate-950 overflow-auto`}>
      <div className="w-full max-w-2xl mx-4 my-8">
        {/* Main Card */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl p-12 border border-gray-200 dark:border-gray-700">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-3xl flex items-center justify-center shadow-xl transform hover:scale-110 transition-transform duration-300">
              <Lock size={52} className="text-white" />
            </div>
          </div>

          {/* Header */}
          <h1 className="text-5xl font-black text-gray-900 dark:text-white text-center mb-3">AI Search Copilot</h1>

          {/* Tabs */}
          <div className="flex gap-2 mb-8 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
            <button
              onClick={() => setShowTab('login')}
              className={`flex-1 py-2 px-4 rounded-md font-bold transition-all ${
                showTab === 'login'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setShowTab('register')}
              className={`flex-1 py-2 px-4 rounded-md font-bold transition-all ${
                showTab === 'register'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* LOGIN TAB */}
          {showTab === 'login' && (
            <>
              <p className="text-gray-600 dark:text-gray-400 text-center mb-8 font-medium text-lg">Sign in to your account</p>

              {/* Login Method Toggle */}
              <div className="flex gap-2 mb-6 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
                <button
                  type="button"
                  onClick={() => setLoginMethod('api')}
                  className={`flex-1 py-2 px-3 rounded-md font-bold transition-all ${
                    loginMethod === 'api'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  API Key
                </button>
                <button
                  type="button"
                  onClick={() => setLoginMethod('password')}
                  className={`flex-1 py-2 px-3 rounded-md font-bold transition-all ${
                    loginMethod === 'password'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  Username
                </button>
              </div>

              <form onSubmit={(e) => {
                e.preventDefault()
                if (loginMethod === 'api') {
                  onLogin(apiKey)
                } else {
                  onLogin({ username: loginUsername, password: loginPassword })
                }
              }} className="space-y-6">
                {/* API Key Login */}
                {loginMethod === 'api' && (
                  <div>
                    <label className="block text-base font-bold text-gray-700 dark:text-gray-300 mb-3">API Key</label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="sk-demo-key-12345"
                        className="w-full px-5 py-3.5 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 text-base"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-3.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                      >
                        {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                      </button>
                    </div>
                  </div>
                )}

                {/* Username/Password Login */}
                {loginMethod === 'password' && (
                  <>
                    <div>
                      <label className="block text-base font-bold text-gray-700 dark:text-gray-300 mb-3">Username</label>
                      <input
                        type="text"
                        value={loginUsername}
                        onChange={(e) => setLoginUsername(e.target.value)}
                        placeholder="johndoe"
                        className="w-full px-5 py-3.5 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 text-base"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-base font-bold text-gray-700 dark:text-gray-300 mb-3">Password</label>
                      <div className="relative">
                        <input
                          type={showPassword ? 'text' : 'password'}
                          value={loginPassword}
                          onChange={(e) => setLoginPassword(e.target.value)}
                          placeholder="••••••••"
                          className="w-full px-5 py-3.5 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 text-base"
                          required
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-3.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                        >
                          {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                        </button>
                      </div>
                    </div>
                  </>
                )}

                {/* Demo Key Info */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-600 p-4 rounded-lg">
                  <p className="text-xs font-bold text-blue-900 dark:text-blue-300 mb-2">💡 Demo API Key:</p>
                  <div className="flex items-center justify-between gap-2">
                    <code className="text-sm text-blue-800 dark:text-blue-200 font-mono font-bold flex-1 break-all">
                      sk-demo-key-12345
                    </code>
                    <button
                      type="button"
                      onClick={() => {
                        setApiKey('sk-demo-key-12345')
                        copyToClipboard('sk-demo-key-12345')
                      }}
                      className="flex-shrink-0 p-2 hover:bg-blue-100 dark:hover:bg-blue-800/40 rounded-lg transition-colors"
                    >
                      <Copy size={18} className="text-blue-600 dark:text-blue-400" />
                    </button>
                  </div>
                </div>

                {/* Error Message */}
                {loginError && (
                  <div className="p-4 bg-red-100 dark:bg-red-900/30 border-2 border-red-400 dark:border-red-600 rounded-xl text-red-700 dark:text-red-300 text-sm font-medium flex items-start gap-3">
                    <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
                    <span>{loginError}</span>
                  </div>
                )}

                {/* Sign In Button */}
                <button
                  type="submit"
                  disabled={isLoggingIn || !apiKey}
                  className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 text-white font-bold py-4 px-4 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-105 text-lg"
                >
                  {isLoggingIn ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-r-transparent rounded-full animate-spin"></div>
                      Signing in...
                    </span>
                  ) : (
                    'Sign In'
                  )}
                </button>
              </form>
            </>
          )}

          {/* REGISTER TAB */}
          {showTab === 'register' && (
            <>
              <p className="text-gray-600 dark:text-gray-400 text-center mb-6 font-medium">Create a new account</p>
              <form onSubmit={(e) => {
                e.preventDefault()
                onRegister({ username, email, password, department })
              }} className="space-y-4">
                {/* Username */}
                <div>
                  <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Username</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="john_doe"
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                      required
                    />
                    <User size={20} className="absolute right-3 top-3.5 text-gray-400" />
                  </div>
                </div>

                {/* Email */}
                <div>
                  <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Email</label>
                  <div className="relative">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="john@example.com"
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                      required
                    />
                    <Mail size={20} className="absolute right-3 top-3.5 text-gray-400" />
                  </div>
                </div>

                {/* Department */}
                <div>
                  <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Department</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      placeholder="Platform/DevOps"
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                    />
                    <Building2 size={20} className="absolute right-3 top-3.5 text-gray-400" />
                  </div>
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Password</label>
                  <div className="relative">
                    <input
                      type={showRegPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowRegPassword(!showRegPassword)}
                      className="absolute right-3 top-3.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                    >
                      {showRegPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                    </button>
                  </div>
                </div>

                {/* Error Message */}
                {registrationError && (
                  <div className="p-4 bg-red-100 dark:bg-red-900/30 border-2 border-red-400 dark:border-red-600 rounded-xl text-red-700 dark:text-red-300 text-sm font-medium flex items-start gap-3">
                    <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
                    <span>{registrationError}</span>
                  </div>
                )}

                {/* Register Button */}
                <button
                  type="submit"
                  disabled={isRegistering || !username || !email || !password}
                  className="w-full bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 hover:from-green-700 hover:via-emerald-700 hover:to-teal-700 text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  {isRegistering ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-r-transparent rounded-full animate-spin"></div>
                      Creating account...
                    </span>
                  ) : (
                    'Create Account'
                  )}
                </button>
              </form>
            </>
          )}

          {/* Footer Info */}
          <div className="text-center mt-6 text-gray-500 dark:text-gray-400 text-xs">
            <p>🔒 Your data is encrypted and secure</p>
          </div>
        </div>
      </div>
    </div>
  )
}
