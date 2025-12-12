import gradio as gr
import shutil
import os
import time
from core.dataset_loader import DatasetLoader

def render():
    # We create a loader instance but we will actually store it in state
    
    with gr.Accordion("2. Input Dataset", open=True):
        file_upload = gr.File(label="Upload JSON Dataset", file_types=[".json"], type="filepath")
        dataset_info = gr.Textbox(label="Dataset Info", interactive=False)
        dataset_state = gr.State() # Stores the DatasetLoader instance

    def handle_upload(file_path):
        if file_path is None:
            return "No file uploaded.", None
        
        # Copy to a local temp file to ensure stability
        os.makedirs("temp", exist_ok=True)
        local_path = os.path.join("temp", "uploaded_dataset.json")
        
        # Retry logic for Windows file locking issues
        copied = False
        last_error = None
        for i in range(5):
            try:
                # copyfile is less strict about metadata/permissions than copy
                shutil.copyfile(file_path, local_path)
                copied = True
                break
            except PermissionError as e:
                last_error = e
                time.sleep(0.5)
            except Exception as e:
                return f"Failed to process upload: {str(e)}", None
        
        if not copied:
             return f"Failed to process upload after retries: {str(last_error)}", None

        loader = DatasetLoader()
        success, msg = loader.load(local_path)
        return msg, loader

    file_upload.upload(handle_upload, inputs=[file_upload], outputs=[dataset_info, dataset_state])

    return file_upload, dataset_info, dataset_state
