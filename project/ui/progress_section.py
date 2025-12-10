import gradio as gr

def render():
    with gr.Accordion("5. Progress", open=True):
        progress_df = gr.Dataframe(
            headers=["Model", "Progress", "Completed/Total", "ETA", "Status"],
            datatype=["str", "str", "str", "str", "str"],
            interactive=False,
            label="Collection Progress"
        )
    return progress_df
