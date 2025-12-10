import gradio as gr

def render():
    with gr.Accordion("4. Collection Control", open=True):
        execution_mode = gr.Radio(choices=["Sequential", "Parallel"], value="Sequential", label="Execution Mode")
        start_btn = gr.Button("Start Collection", variant="primary")
    
    return execution_mode, start_btn
