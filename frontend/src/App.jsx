import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

export default function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(false)
    const [currentView, setCurrentView] = useState('dashboard')
    const [user, setUser] = useState(null)
    const [agents, setAgents] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [loginEmail, setLoginEmail] = useState('demo@example.com')
    const [loginPassword, setLoginPassword] = useState('demo123456')

    const handleLogin = async (e) => {
        e.preventDefault()
        try {
            setLoading(true)
            setError(null)
            setUser({ email: loginEmail })
            setIsLoggedIn(true)
            setCurrentView('dashboard')
        } catch (err) {
            setError('Login failed: ' + (err.message || 'Unknown error'))
        } finally {
            setLoading(false)
        }
    }

    const handleLogout = () => {
        setIsLoggedIn(false)
        setUser(null)
        setCurrentView('dashboard')
        setLoginEmail('demo@example.com')
        setLoginPassword('demo123456')
    }

    const fetchAgents = async () => {
        try {
            setLoading(true)
            const response = await axios.get('/api/marketplace/agents')
            setAgents(response.data.agents || [])
            setError(null)
        } catch (err) {
            setError('Failed to load agents: ' + (err.message || 'Unknown error'))
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (isLoggedIn && currentView === 'agents') {
            fetchAgents()
        }
    }, [currentView, isLoggedIn])

    return (
        <div className="app">
            {!isLoggedIn ? (
                // LOGIN SCREEN
                <div className="login-container">
                    <div className="login-box">
                        <h1>🚀 Welcome</h1>
                        <p>Choose your platform</p>

                        <form onSubmit={handleLogin}>
                            <input
                                type="email"
                                placeholder="Email"
                                value={loginEmail}
                                onChange={(e) => setLoginEmail(e.target.value)}
                                required
                            />
                            <input
                                type="password"
                                placeholder="Password"
                                value={loginPassword}
                                onChange={(e) => setLoginPassword(e.target.value)}
                                required
                            />
                            <button type="submit" disabled={loading}>
                                {loading ? 'Logging in...' : 'Login'}
                            </button>
                            {error && <div className="error-message">{error}</div>}
                        </form>

                        <p className="demo-hint">Demo: demo@example.com / demo123456</p>
                    </div>
                </div>
            ) : (
                // MAIN APP
                <>
                    <header className="header">
                        <div className="header-content">
                            <h1>Welcome, {user?.email}!</h1>
                            <button onClick={handleLogout} className="logout-btn">Logout</button>
                        </div>
                    </header>

                    <nav className="project-nav">
                        <button
                            className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
                            onClick={() => setCurrentView('dashboard')}
                        >
                            📊 Dashboard
                        </button>
                        <button
                            className={`nav-btn ${currentView === 'agents' ? 'active' : ''}`}
                            onClick={() => setCurrentView('agents')}
                        >
                            🤖 AI Dev Agents
                        </button>
                        <button
                            className={`nav-btn ${currentView === 'dutyguard' ? 'active' : ''}`}
                            onClick={() => setCurrentView('dutyguard')}
                        >
                            💼 DutyGuard AI
                        </button>
                    </nav>

                    <main className="main">
                        <div className="container">
                            {/* DASHBOARD VIEW */}
                            {currentView === 'dashboard' && (
                                <div className="dashboard">
                                    <h2>Select a Project</h2>
                                    <div className="project-cards">
                                        <div className="project-card" onClick={() => setCurrentView('agents')}>
                                            <div className="project-icon">🤖</div>
                                            <h3>AI Dev Agents Marketplace</h3>
                                            <p>Discover and purchase AI agents to automate your development workflow</p>
                                            <button>Go to Marketplace →</button>
                                        </div>

                                        <div className="project-card" onClick={() => setCurrentView('dutyguard')}>
                                            <div className="project-icon">💼</div>
                                            <h3>DutyGuard AI</h3>
                                            <p>Global tariff audit engine for automated duty recovery and compliance</p>
                                            <button>Go to DutyGuard →</button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* AI AGENTS VIEW */}
                            {currentView === 'agents' && (
                                <>
                                    <div className="section-header">
                                        <h2>AI Dev Agents Marketplace</h2>
                                        <p>Discover powerful AI agents to boost your development</p>
                                    </div>

                                    {loading && (
                                        <div className="loading">
                                            <div className="spinner"></div>
                                            <p>Loading agents...</p>
                                        </div>
                                    )}

                                    {error && (
                                        <div className="error">
                                            <p>{error}</p>
                                            <button onClick={fetchAgents}>Retry</button>
                                        </div>
                                    )}

                                    {!loading && !error && agents.length === 0 && (
                                        <div className="empty">
                                            <p>No agents available yet</p>
                                        </div>
                                    )}

                                    {!loading && !error && agents.length > 0 && (
                                        <div className="agents-grid">
                                            {agents.map(agent => (
                                                <div key={agent.id} className="agent-card">
                                                    <div className="agent-icon">
                                                        {agent.displayName.substring(0, 2)}
                                                    </div>
                                                    <h3>{agent.displayName}</h3>
                                                    <p className="description">{agent.description}</p>
                                                    <div className="agent-meta">
                                                        <span>⭐ {agent.avgRating}</span>
                                                        <span>📥 {agent.totalInstalls}</span>
                                                    </div>
                                                    <div className="agent-footer">
                                                        <span className="price">${agent.price}</span>
                                                        <button className="btn-purchase">Purchase</button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            )}

                            {/* DUTYGUARD VIEW */}
                            {currentView === 'dutyguard' && (
                                <div className="dutyguard-section">
                                    <div className="section-header">
                                        <h2>💼 DutyGuard AI</h2>
                                        <p>Global Tariff Audit Engine</p>
                                    </div>

                                    <div className="dutyguard-content">
                                        <div className="feature-card">
                                            <h3>🔍 Automated Duty Recovery</h3>
                                            <p>Recover overpaid customs duties through systematic audits</p>
                                        </div>

                                        <div className="feature-card">
                                            <h3>📋 Trade Compliance</h3>
                                            <p>Validate shipments against global tariff rules</p>
                                        </div>

                                        <div className="feature-card">
                                            <h3>💰 Tariff Optimization</h3>
                                            <p>Find duty-saving routes and classifications</p>
                                        </div>

                                        <div className="feature-card">
                                            <h3>⚡ Batch Processing</h3>
                                            <p>Process thousands of shipments in minutes</p>
                                        </div>

                                        <button className="btn-primary" onClick={() => alert('DutyGuard AI Coming Soon!')}>
                                            Launch DutyGuard AI
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </main>

                    <footer className="footer">
                        <p>© 2026 AI Dev Agents & DutyGuard AI - Powering Your Workflow</p>
                    </footer>
                </>
            )}
        </div>
    )
}
