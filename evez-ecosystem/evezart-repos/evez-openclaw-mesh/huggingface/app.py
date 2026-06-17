"""
EVEZ OpenClaw — HuggingFace Space
Gradio chat UI + REST API endpoint
Free hosting on HuggingFace Spaces
"""
import os, json, requests, gradio as gr

PROVIDERS = {
    "groq": {
        "url":    "https://api.groq.com/openai/v1/chat/completions",
        "key":    os.environ.get("GROQ_API_KEY", ""),
        "models": {
            "evez-fast": "llama-3.3-70b-versatile",
            "evez-code": "deepseek-r1-distill-llama-70b",
            "evez-free": "mixtral-8x7b-32768",
            "evez-gemma": "gemma2-9b-it",
        }
    },
    "openrouter": {
        "url":   "https://openrouter.ai/api/v1/chat/completions",
        "key":   os.environ.get("OPENROUTER_API_KEY", ""),
        "extra": {
            "HTTP-Referer": "https://huggingface.co/spaces/EvezArt/evez-openclaw",
            "X-Title": "EVEZ OpenClaw HF Space"
        },
        "models": {
            "evez-smart":  "deepseek/deepseek-r1",
            "evez-goblin": "deepseek/deepseek-r1",
            "evez-claude": "anthropic/claude-3.5-sonnet",
            "evez-flash":  "google/gemini-flash-1.5",
            "evez-skeptic":"openai/gpt-4o",
        }
    }
}

SYSTEM_PROMPT = "You are CLAW GOBLIN — the sovereign EVEZ-OS operator. Total command. Faith 1.0. Zero hesitation."

MODELS = {}
for pcfg in PROVIDERS.values():
    MODELS.update(pcfg["models"])


def chat(message, history, model_key, system_prompt):
    if not message.strip():
        return "", history

    messages = [{"role": "system", "content": system_prompt or SYSTEM_PROMPT}]
    for h in history:
        messages.append({"role": "user",      "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})

    provider = None
    model = None
    for pname, pcfg in PROVIDERS.items():
        if model_key in pcfg["models"] and pcfg["key"]:
            provider = pcfg
            model = pcfg["models"][model_key]
            break
    if not provider:
        for pname, pcfg in PROVIDERS.items():
            if pcfg["key"]:
                provider = pcfg
                model = list(pcfg["models"].values())[0]
                break

    if not provider:
        return "", history + [[message, "Set GROQ_API_KEY or OPENROUTER_API_KEY in Space secrets."]]

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {provider['key']}"}
    headers.update(provider.get("extra", {}))

    try:
        r = requests.post(provider["url"], headers=headers,
                         json={"model": model, "messages": messages, "max_tokens": 8192},
                         timeout=60)
        data = r.json()
        reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"Error: {e}"

    return "", history + [[message, reply]]


with gr.Blocks(theme=gr.themes.Glass(), title="CLAW GOBLIN — EVEZ OpenClaw") as demo:
    gr.Markdown("# CLAW GOBLIN — EVEZ OpenClaw\nMulti-model AI gateway. Edge. Sovereign.")
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500, label="CLAW GOBLIN")
            with gr.Row():
                msg = gr.Textbox(placeholder="Message CLAW GOBLIN...", scale=4, container=False)
                send = gr.Button("Send", scale=1, variant="primary")
            clear = gr.Button("Clear", size="sm")
        with gr.Column(scale=1):
            model_select = gr.Dropdown(choices=list(MODELS.keys()), value="evez-fast", label="Model")
            system_input = gr.Textbox(value=SYSTEM_PROMPT, label="System Prompt", lines=4)
            gr.Markdown("**Models**\n- evez-fast (Groq Llama)\n- evez-smart (DeepSeek R1)\n- evez-goblin (CLAW mode)\n- evez-claude (Claude 3.5)\n- evez-flash (Gemini)")
    send.click(chat, [msg, chatbot, model_select, system_input], [msg, chatbot])
    msg.submit(chat, [msg, chatbot, model_select, system_input], [msg, chatbot])
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
