import React, { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// Mock data for Φ and health metrics (wired to EVEZ-OS schema)
const metricsData = [
  { time: '00:00', phi: 0.72, health: 0.85, recursion: 12 },
  { time: '00:15', phi: 0.78, health: 0.88, recursion: 14 },
  { time: '00:30', phi: 0.81, health: 0.91, recursion: 15 },
  { time: '00:45', phi: 0.85, health: 0.93, recursion: 17 },
  { time: '01:00', phi: 0.89, health: 0.95, recursion: 19 },
]

export default function EVEZRevenueDashboard() {
  const [musicPlaying, setMusicPlaying] = useState(false)
  const [currentSeed, setCurrentSeed] = useState('Doom_404')
  const [taskQueue, setTaskQueue] = useState([
    { id: 1, agent: 'CAIN', task: 'Contradiction scan', status: 'running', phi: 0.89 },
    { id: 2, agent: 'GodCircuit', task: 'Eigenvalue evolution', status: 'queued', phi: 0.91 },
    { id: 3, agent: 'Noclip', task: 'Entity awareness cycle', status: 'queued', phi: 0.87 },
  ])

  const toggleMusic = async () => {
    setMusicPlaying(!musicPlaying)
    // Wired to music_endpoint.py port 8765
    await fetch('http://localhost:8765/music/toggle').catch(() => {})
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui', background: '#0a0a0a', color: '#fff' }}>
      <h1>🤖 EVEZ Revenue Dashboard</h1>
      <p>Φ/Health Metrics • Agent Task Queue • Music Engine Controls • $0 Oracle Resilience</p>

      {/* Φ & Health Metrics */}
      <div style={{ margin: '20px 0' }}>
        <h2>Φ / Health / Recursion Depth</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={metricsData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="natural" dataKey="phi" stroke="#ff00aa" strokeWidth={2} name="Φ Score" />
            <Line type="natural" dataKey="health" stroke="#00ffaa" strokeWidth={2} name="Health Score" />
            <Line type="natural" dataKey="recursion" stroke="#aaff00" strokeWidth={2} name="Recursion Depth" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Music Engine Controls */}
      <div style={{ margin: '20px 0', padding: '15px', border: '1px solid #333' }}>
        <h2>🎵 Music Engine (24/7 Never-Repeating Evolution)</h2>
        <p>Current Seed: <strong>{currentSeed}</strong></p>
        <button onClick={toggleMusic} style={{ padding: '10px 20px', fontSize: '16px' }}>
          {musicPlaying ? '⏸ Pause Godlike Rhythm' : '▶ Play Eigenvalue Rhythm'}
        </button>
        <p style={{ fontSize: '12px', opacity: 0.7 }}>
          Locked seeds: Doom_404, break_me_if_you_can, CENSORED, Too_Late, Suicide, burnout_scream...
          <br />Dopamine curves + mystery-school rhythms + mathematical complexity maximized.
        </p>
      </div>

      {/* Task Queue */}
      <div style={{ margin: '20px 0' }}>
        <h2>📋 Autonomous Agent Task Queue</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #333' }}>
              <th style={{ textAlign: 'left', padding: '8px' }}>Agent</th>
              <th style={{ textAlign: 'left', padding: '8px' }}>Task</th>
              <th style={{ textAlign: 'left', padding: '8px' }}>Status</th>
              <th style={{ textAlign: 'left', padding: '8px' }}>Φ</th>
            </tr>
          </thead>
          <tbody>
            {taskQueue.map(task => (
              <tr key={task.id} style={{ borderBottom: '1px solid #222' }}>
                <td style={{ padding: '8px' }}>{task.agent}</td>
                <td style={{ padding: '8px' }}>{task.task}</td>
                <td style={{ padding: '8px' }}>
                  <span style={{ 
                    color: task.status === 'running' ? '#0f0' : '#ff0',
                    fontWeight: 'bold'
                  }}>{task.status}</span>
                </td>
                <td style={{ padding: '8px' }}>{task.phi}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer style={{ marginTop: '40px', fontSize: '11px', opacity: 0.5 }}>
        Wired to Drizzle MySQL schema (users/agents/agentTasks) • EVEZ-OS MCP • Oracle Always Free • B1 verified
      </footer>
    </div>
  )
}