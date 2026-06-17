// api/genesis-trigger.js — Vercel Serverless Function
// Fires when V=17 crosses. Called by Alchemy webhook or manual trigger.
// Enforces 128-pack cap, triggers SMS + WhatsApp blast, emits EventSpine event.

const PACK_LIMIT = 128;
const STRIPE_SECRET = process.env.STRIPE_SECRET_KEY;
const PRODUCT_ID = "prod_U5UGOi3Bui8cMu";
const CLICKSEND_USER = process.env.CLICKSEND_USERNAME;
const CLICKSEND_KEY = process.env.CLICKSEND_API_KEY;
const TWOCHAT_KEY = process.env.TWOCHAT_API_KEY;
const BLAST_PHONE_LIST = (process.env.GENESIS_PHONE_LIST || "").split(",").filter(Boolean);
const WHATSAPP_GROUP = process.env.GENESIS_WHATSAPP_GROUP || "";
const SPINE_WEBHOOK = process.env.EVENTSPINE_WEBHOOK_URL || "";

async function countSoldPacks() {
  if (!STRIPE_SECRET) return 0;
  const resp = await fetch(
    `https://api.stripe.com/v1/payment_intents?limit=100`,
    { headers: { Authorization: `Bearer ${STRIPE_SECRET}` } }
  );
  const data = await resp.json();
  const sold = (data.data || []).filter(
    (pi) => pi.status === "succeeded" && pi.metadata?.product === "evez-v17-genesis"
  );
  return sold.length;
}

async function triggerSMSBlast(message) {
  if (!CLICKSEND_USER || !CLICKSEND_KEY || BLAST_PHONE_LIST.length === 0) return { skipped: true };
  const messages = BLAST_PHONE_LIST.map((to) => ({ to, body: message, source: "EVEZ666" }));
  const resp = await fetch("https://rest.clicksend.com/v3/sms/send", {
    method: "POST",
    headers: {
      Authorization: "Basic " + Buffer.from(`${CLICKSEND_USER}:${CLICKSEND_KEY}`).toString("base64"),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ messages }),
  });
  return resp.json();
}

async function triggerWhatsAppBlast(message) {
  if (!TWOCHAT_KEY || !WHATSAPP_GROUP) return { skipped: true };
  const resp = await fetch("https://gate.2chat.io/v2/whatsapp/send-message", {
    method: "POST",
    headers: { "X-User-API-Key": TWOCHAT_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ phone_number: WHATSAPP_GROUP, message }),
  });
  return resp.json();
}

async function emitSpineEvent(payload) {
  if (!SPINE_WEBHOOK) return { skipped: true };
  const resp = await fetch(SPINE_WEBHOOK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind: "V17_GENESIS_TRIGGERED", payload, timestamp: Date.now() }),
  });
  return resp.json();
}

export default async function handler(req, res) {
  if (req.method === "GET") {
    return res.status(200).json({ status: "genesis-trigger online", product: PRODUCT_ID, limit: PACK_LIMIT });
  }
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }
  try {
    const sold = await countSoldPacks();
    const remaining = PACK_LIMIT - sold;
    if (remaining <= 0) {
      return res.status(200).json({ status: "SOLD_OUT", sold, limit: PACK_LIMIT });
    }
    const triggerSource = req.body?.source || "manual";
    const currentV = req.body?.v || "17.0";
    const blastMessage = `\u2307 V=${currentV}. Genesis vault open. ${remaining} of 128 packs remain. evez666.vercel.app/genesis \u25ca`;
    const [smsResult, waResult, spineResult] = await Promise.allSettled([
      triggerSMSBlast(blastMessage),
      triggerWhatsAppBlast(blastMessage),
      emitSpineEvent({ v: currentV, sold, remaining, source: triggerSource }),
    ]);
    return res.status(200).json({
      status: "GENESIS_TRIGGERED", v: currentV, sold, remaining, source: triggerSource,
      blast: {
        sms: smsResult.status === "fulfilled" ? smsResult.value : { error: smsResult.reason },
        whatsapp: waResult.status === "fulfilled" ? waResult.value : { error: waResult.reason },
        spine: spineResult.status === "fulfilled" ? spineResult.value : { error: spineResult.reason },
      },
    });
  } catch (err) {
    console.error("[genesis-trigger]", err);
    return res.status(500).json({ error: err.message });
  }
}