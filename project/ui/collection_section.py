import gradio as gr

def render():
    with gr.Accordion("4. Collection Control", open=True):
        execution_mode = gr.Radio(choices=["Sequential", "Parallel"], value="Sequential", label="Execution Mode")
        with gr.Row():
            start_btn = gr.Button("Start Collection", variant="primary")
            stop_btn = gr.Button("Stop Collection", variant="stop")
        
        stop_dropdown = gr.Dropdown(label="Select Model to Stop", choices=[], interactive=False, visible=True)
        stop_status = gr.Markdown("", visible=True)
    
    return execution_mode, start_btn, stop_btn, stop_dropdown, stop_status
