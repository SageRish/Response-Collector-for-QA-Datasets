import gradio as gr

def render():
    with gr.Accordion("1. Global Settings", open=True):
        with gr.Row():
            short_tokens = gr.Number(value=100, label="Short Response Max Tokens", precision=0)
            long_tokens = gr.Number(value=500, label="Long Response Max Tokens", precision=0)
        system_prompt = gr.Textbox(label="System Prompt Override (Optional)", placeholder="You are a helpful assistant...", lines=2)
    return short_tokens, long_tokens, system_prompt
