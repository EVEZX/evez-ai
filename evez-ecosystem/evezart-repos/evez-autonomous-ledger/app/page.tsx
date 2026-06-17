export default function HomePage() {
  return (
    <main style={{ padding: 24, fontFamily: 'sans-serif' }}>
      <h1>EVEZ Operator</h1>
      <p>Autopilot operator spine is live.</p>
      <p>Use <code>/api/health</code> to verify runtime health.</p>
      <p>
        Use <code>/api/run</code> with a POST body containing{' '}
        <code>{'{"task":"..."}'}</code> to test route selection.
      </p>
    </main>
  );
}
