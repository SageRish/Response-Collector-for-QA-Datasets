import gradio as gr

def render():
    with gr.Accordion("6. Logs", open=True):
        logs_output = gr.TextArea(label="Process Logs", interactive=False, lines=10)
    return logs_output
