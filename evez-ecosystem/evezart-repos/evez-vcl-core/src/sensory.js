// EVEZ VCL Sensory — YouTube live chat + viewer analytics
import fetch from 'node-fetch';

const YT_BASE = 'https://www.googleapis.com/youtube/v3';

// Refresh token if needed (stored as env, rotated via Supabase)
let _token = process.env.YOUTUBE_TOKEN;
let _liveChatId = null;
let _pageToken = null;

export async function getLiveChatId(broadcastId) {
  if (_liveChatId) return _liveChatId;
  try {
    const r = await fetch(
      `${YT_BASE}/liveBroadcasts?part=snippet&id=${broadcastId}&key=${process.env.YT_API_KEY || ''}`,
      { headers: { Authorization: `Bearer ${_token}` } }
    );
    const d = await r.json();
    _liveChatId = d.items?.[0]?.snippet?.liveChatId;
    return _liveChatId;
  } catch (e) {
    console.error('[sensory] getLiveChatId error:', e.message);
    return null;
  }
}

export async function fetchChatMessages(liveChatId) {
  try {
    const params = new URLSearchParams({ part: 'snippet', liveChatId, maxResults: '200' });
    if (_pageToken) params.set('pageToken', _pageToken);
    const r = await fetch(`${YT_BASE}/liveChat/messages?${params}`, {
      headers: { Authorization: `Bearer ${_token}` }
    });
    const d = await r.json();
    if (d.error) {
      console.error('[sensory] chat error:', d.error.message);
      return [];
    }
    _pageToken = d.nextPageToken;
    return (d.items || []).map(i => i.snippet?.displayMessage || '').filter(Boolean);
  } catch (e) {
    console.error('[sensory] fetchChat error:', e.message);
    return [];
  }
}

export async function getViewerCount(broadcastId) {
  try {
    const r = await fetch(
      `${YT_BASE}/videos?part=liveStreamingDetails&id=${broadcastId}`,
      { headers: { Authorization: `Bearer ${_token}` } }
    );
    const d = await r.json();
    return parseInt(d.items?.[0]?.liveStreamingDetails?.concurrentViewers || '0', 10);
  } catch (e) { return 0; }
}

export async function analyzeSentiment(messages, groqApiKey) {
  if (!messages.length || !groqApiKey) return 0;
  try {
    const r = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${groqApiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [{
          role: 'user',
          content: `Rate the collective sentiment of these chat messages from -1.0 (very negative/chaotic/aggressive) to +1.0 (very positive/calm/peaceful). Reply with ONLY a decimal number. Messages: ${messages.slice(-20).join(' | ')}`
        }],
        max_tokens: 10,
        temperature: 0,
      })
    });
    const d = await r.json();
    const val = parseFloat(d.choices?.[0]?.message?.content?.trim());
    return isNaN(val) ? 0 : Math.max(-1, Math.min(1, val));
  } catch (e) { return 0; }
}
