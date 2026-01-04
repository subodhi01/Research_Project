import React, { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { login } from "../../api/auth"

function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [loginMetrics, setLoginMetrics] = useState({
    password_length: 0,
    typing_start: null,
    typing_end: null,
    keystrokes: [],
    caps_lock_detected: false,
    browser_tabs: 1,
    keyboard_language: "EN",
  })
  const navigate = useNavigate()
  const passwordRef = useRef(null)
  const usernameRef = useRef(null)
  const loginAttemptsRef = useRef(0)

  useEffect(() => {
    const token = localStorage.getItem("authToken")
    if (token) {
      navigate("/")
    }

    const detectKeyboardLanguage = () => {
      try {
        const lang = navigator.language || navigator.userLanguage || "en-US"
        const langCode = lang.split("-")[0].toUpperCase()
        return langCode === "EN" ? "EN" : langCode
      } catch {
        return "EN"
      }
    }

    const detectBrowserTabs = () => {
      try {
        if (typeof Storage !== "undefined" && localStorage) {
          const tabCount = localStorage.getItem("browserTabCount")
          if (tabCount) {
            const count = parseInt(tabCount, 10)
            if (!isNaN(count) && count > 0) {
              return count
            }
          }
        }
        return 1
      } catch {
        return 1
      }
    }

    setLoginMetrics((prev) => ({
      ...prev,
      keyboard_language: detectKeyboardLanguage(),
      browser_tab_count: detectBrowserTabs(),
    }))
  }, [navigate])

  const detectCapsLock = (e) => {
    const isCapsLock = e.getModifierState && e.getModifierState("CapsLock")
    if (isCapsLock !== undefined) {
      setLoginMetrics((prev) => ({ ...prev, caps_lock_detected: isCapsLock }))
    }
    
    const char = String.fromCharCode(e.keyCode || e.which)
    if (char >= "A" && char <= "Z" && !e.shiftKey) {
      setLoginMetrics((prev) => ({ ...prev, caps_lock_detected: true }))
    } else if (char >= "a" && char <= "z" && e.shiftKey) {
      setLoginMetrics((prev) => ({ ...prev, caps_lock_detected: false }))
    }
  }

  const handlePasswordKeyDown = (e) => {
    detectCapsLock(e)
    const timestamp = Date.now()
    setLoginMetrics((prev) => ({
      ...prev,
      keystrokes: [...prev.keystrokes, { key: e.key, timestamp }],
    }))
  }

  const handlePasswordChange = (e) => {
    const value = e.target.value
    if (!loginMetrics.typing_start) {
      setLoginMetrics((prev) => ({ ...prev, typing_start: Date.now() }))
    }
    setPassword(value)
    setLoginMetrics((prev) => ({ ...prev, password_length: value.length }))
  }

  const handlePasswordKeyUp = (e) => {
    detectCapsLock(e)
  }

  const handlePasswordBlur = () => {
    if (loginMetrics.typing_start) {
      setLoginMetrics((prev) => ({ ...prev, typing_end: Date.now() }))
    }
  }

  const calculateTypingSpeed = () => {
    if (loginMetrics.keystrokes.length < 2) {
      if (loginMetrics.typing_start && loginMetrics.typing_end) {
        const duration = (loginMetrics.typing_end - loginMetrics.typing_start) / 1000
        if (duration > 0) {
          const words = password.length / 5
          const wpm = (words / duration) * 60
          return Math.max(30, Math.min(150, wpm))
        }
      }
      return 60
    }

    const keystrokes = loginMetrics.keystrokes
    if (keystrokes.length < 2) return 60

    const firstKey = keystrokes[0]
    const lastKey = keystrokes[keystrokes.length - 1]
    const duration = (lastKey.timestamp - firstKey.timestamp) / 1000

    if (duration <= 0) return 60

    const characters = password.length
    const words = characters / 5
    const wpm = (words / duration) * 60

    return Math.max(30, Math.min(150, wpm))
  }

  const analyzePassword = () => {
    const hasSpecialChars = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)
    const hasNumbers = /[0-9]/.test(password)
    const hasUpperCase = /[A-Z]/.test(password)
    const hasLowerCase = /[a-z]/.test(password)

    return {
      length: password.length,
      has_special: hasSpecialChars,
      has_numbers: hasNumbers,
      has_upper: hasUpperCase,
      has_lower: hasLowerCase,
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    loginAttemptsRef.current += 1

    try {
      const typingSpeed = calculateTypingSpeed()
      const passwordAnalysis = analyzePassword()
      
      const generateChallengeSequence = () => {
        if (loginMetrics.keystrokes.length < 2) {
          return ""
        }
        const intervals = []
        for (let i = 1; i < loginMetrics.keystrokes.length; i++) {
          const interval = loginMetrics.keystrokes[i].timestamp - loginMetrics.keystrokes[i - 1].timestamp
          const normalized = Math.min(Math.max(Math.floor(interval / 50), 1), 9)
          intervals.push(normalized)
        }
        return intervals.slice(0, 10).join("-")
      }

      const zeroTrustMetrics = {
        password_length: passwordAnalysis.length,
        used_special_characters: passwordAnalysis.has_special ? "yes" : "no",
        keyboard_language: loginMetrics.keyboard_language,
        login_attempts: loginAttemptsRef.current,
        was_capslock_on: loginMetrics.caps_lock_detected ? "yes" : "no",
        browser_tab_count: loginMetrics.browser_tabs,
        challenge_sequence: generateChallengeSequence(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC+0",
        typing_speed_wpm: typingSpeed,
      }

      console.log("Zero Trust Metrics Captured:", {
        ...zeroTrustMetrics,
        password_analysis: passwordAnalysis,
        keystroke_count: loginMetrics.keystrokes.length,
      })

      const result = await login(username, password, zeroTrustMetrics)
      
      localStorage.setItem("authToken", result.access_token)
      localStorage.setItem("finsightCurrentUser", JSON.stringify(result.user))
      window.dispatchEvent(new Event("finsight-current-user-changed"))
      
      navigate("/")
    } catch (err) {
      if (err.response?.status === 403) {
        setError(err.response.data.detail || "Login blocked: High risk detected")
      } else {
        setError(err.response?.data?.detail || "Invalid username or password")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-slate-50 mb-2">Zero Trust Login</h1>
            <p className="text-sm text-slate-400">
              Secure authentication with real-time risk assessment
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Username</label>
              <input
                ref={usernameRef}
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={detectCapsLock}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                required
                autoFocus
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Password</label>
              <input
                ref={passwordRef}
                type="password"
                value={password}
                onChange={handlePasswordChange}
                onKeyDown={handlePasswordKeyDown}
                onKeyUp={handlePasswordKeyUp}
                onBlur={handlePasswordBlur}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                required
              />
              <div className="mt-2 space-y-1">
                <p className="text-xs text-slate-500">
                  Default password: <code className="bg-slate-800 px-1 rounded">password123</code>
                </p>
                {loginMetrics.caps_lock_detected && (
                  <p className="text-xs text-amber-400 flex items-center gap-1">
                    <span>⚠️</span> Caps Lock is ON
                  </p>
                )}
                <div className="text-xs text-slate-600 space-x-2">
                  <span>Length: {password.length}</span>
                  <span>•</span>
                  <span>WPM: {calculateTypingSpeed().toFixed(0)}</span>
                  <span>•</span>
                  <span>Tabs: {loginMetrics.browser_tabs}</span>
                  <span>•</span>
                  <span>Lang: {loginMetrics.keyboard_language}</span>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-rose-500/10 border border-rose-500/40 rounded px-3 py-2 text-sm text-rose-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full px-4 py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Analyzing & Logging in..." : "Login with Zero Trust"}
            </button>
          </form>

          <div className="text-xs text-slate-500 space-y-1 pt-4 border-t border-slate-800">
            <p>
              <strong className="text-slate-400">Auto-detected metrics:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Password length & special characters</li>
              <li>Typing speed (WPM) from keystroke timing</li>
              <li>Caps Lock status detection</li>
              <li>Browser tabs count estimation</li>
              <li>Keyboard language detection</li>
              <li>Login attempt tracking</li>
              <li>All data analyzed by ML risk model</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
