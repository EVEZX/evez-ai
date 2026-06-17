// EVEZ VCL Brain — Supabase persistent state accumulator
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);

const VCL_ID = process.env.VCL_ID || 'fire';

// Load brain state from Supabase (or defaults)
export async function loadBrain() {
  try {
    const { data } = await supabase
      .from('vcl_brain_state')
      .select('*')
      .eq('vcl_id', VCL_ID)
      .single();
    if (data?.params) {
      console.log(`[brain] loaded state for ${VCL_ID}:`, data.params);
      return data.params;
    }
  } catch (e) {
    console.log('[brain] no prior state, using defaults');
  }
  return { energy: 1.0, chaos: 0.5, speed: 1.0, scale: 1.0, mood: 0.5 };
}

// Persist brain state
export async function saveBrain(params) {
  try {
    await supabase
      .from('vcl_brain_state')
      .upsert({
        vcl_id: VCL_ID,
        params,
        updated_at: new Date().toISOString(),
      }, { onConflict: 'vcl_id' });
  } catch (e) {
    console.error('[brain] save error:', e.message);
  }
}

// Log a sensory event
export async function logSensory(type, data) {
  try {
    await supabase.from('vcl_sensory_log').insert({
      vcl_id: VCL_ID,
      event_type: type,
      event_data: data,
      created_at: new Date().toISOString(),
    });
  } catch (e) { /* non-critical */ }
}
