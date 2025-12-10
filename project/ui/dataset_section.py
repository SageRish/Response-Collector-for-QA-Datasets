import gradio as gr
import shutil
import os
from core.dataset_loader import DatasetLoader

def render():
    # We create a loader instance but we will actually store it in state
    
    with gr.Accordion("2. Input Dataset", open=True):
        file_upload = gr.File(label="Upload JSON Dataset", file_types=[".json"], type="filepath")
        dataset_info = gr.Textbox(label="Dataset Info", interactive=False)
        dataset_state = gr.State() # Stores the DatasetLoader instance

    def handle_upload(file):
        if file is None:
            return "No file uploaded.", None
        
        # Copy to a local temp file to ensure stability
        os.makedirs("temp", exist_ok=True)
        local_path = os.path.join("temp", "uploaded_dataset.json")
        try:
            shutil.copy(file, local_path)
        except Exception as e:
            return f"Failed to process upload: {str(e)}", None

        loader = DatasetLoader()
        success, msg = loader.load(local_path)
        return msg, loader

    file_upload.upload(handle_upload, inputs=[file_upload], outputs=[dataset_info, dataset_state])

    return file_upload, dataset_info, dataset_state
