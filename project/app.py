import gradio as gr
import asyncio
import os
from ui import (
    setup_section, dataset_section, models_section,
    collection_section, progress_section, logs_section, theme
)
from core.collector import collect_responses, test_provider
from core.logger import Logger
from core.utils import save_json, format_dataset_output

def create_app():
    with gr.Blocks(title="LLM Response Collector") as app:
        gr.Markdown("# 🤖 Multi-Provider LLM Response Collector")
        
        # 1. Setup
        short_tokens, long_tokens, system_prompt = setup_section.render()
        
        # 2. Dataset
        file_upload, dataset_info, dataset_state = dataset_section.render()
        
        # 3. Models
        alias_input, provider_input, model_name_input, base_url_input, api_key_input, add_btn, models_list, test_btn, models_state = models_section.render()
        
        # 4. Collection
        execution_mode, start_btn = collection_section.render()
        
        # 5. Progress
        progress_df = progress_section.render()
        
        # 6. Logs
        logs_output = logs_section.render()

        # --- Logic ---

        async def run_tests(models):
            if not models:
                yield "No models configured."
                return
            
            logger = Logger()
            logger.log("Testing providers...")
            yield logger.get_logs()
            
            for model in models:
                success, msg = await test_provider(model)
                logger.log(f"[{model.alias}] {msg}")
                yield logger.get_logs()

        test_btn.click(
            run_tests,
            inputs=[models_state],
            outputs=[logs_output]
        )

        async def run_collection(
            short_tokens, long_tokens, system_prompt,
            dataset_loader,
            models,
            execution_mode
        ):
            logger = Logger()
            
            # Validation
            if not dataset_loader:
                logger.log("Error: No dataset loaded.")
                yield {logs_output: logger.get_logs()}
                return
            if not models:
                logger.log("Error: No models configured.")
                yield {logs_output: logger.get_logs()}
                return

            logger.log(f"Starting collection in {execution_mode} mode...")
            yield {logs_output: logger.get_logs()}

            # Initialize progress states
            # Map alias -> list representation
            progress_states = {}
            for m in models:
                progress_states[m.alias] = [m.alias, "0.0%", f"0/{dataset_loader.num_questions}", "-", "Pending"]
            
            def get_progress_data():
                return [progress_states[m.alias] for m in models]
            
            # Initial update
            yield {progress_df: get_progress_data(), logs_output: logger.get_logs()}

            def progress_callback(state):
                progress_states[state.model_alias] = state.to_list()

            async def run_model_task(model):
                try:
                    data, missing = await collect_responses(
                        model, dataset_loader, 
                        int(short_tokens), int(long_tokens), 
                        system_prompt, logger, progress_callback
                    )
                    
                    # Save outputs
                    output_dir = "outputs"
                    save_json(format_dataset_output(model.alias, data), os.path.join(output_dir, f"{model.alias}_dataset.json"))
                    save_json(missing, os.path.join(output_dir, f"{model.alias}_missing_responses.json"))
                    
                except Exception as e:
                    logger.log(f"[{model.alias}] Critical failure: {str(e)}")
                    # Update status to failed
                    current = progress_states[model.alias]
                    current[-1] = "Failed"
                    progress_states[model.alias] = current

            if execution_mode == "Sequential":
                for model in models:
                    task = asyncio.create_task(run_model_task(model))
                    while not task.done():
                        yield {progress_df: get_progress_data(), logs_output: logger.get_logs()}
                        await asyncio.sleep(0.5)
                    await task
            else:
                # Parallel
                # Check for unique providers
                providers = [m.provider for m in models]
                if len(providers) != len(set(providers)):
                    logger.log("Warning: Parallel mode selected but providers are not unique. Rate limits may occur.")
                
                tasks = [asyncio.create_task(run_model_task(m)) for m in models]
                while not all(t.done() for t in tasks):
                    yield {progress_df: get_progress_data(), logs_output: logger.get_logs()}
                    await asyncio.sleep(0.5)
                for t in tasks:
                    await t

            logger.log("All collections finished.")
            yield {progress_df: get_progress_data(), logs_output: logger.get_logs()}

        start_btn.click(
            run_collection,
            inputs=[
                short_tokens, long_tokens, system_prompt,
                dataset_state, models_state, execution_mode
            ],
            outputs=[progress_df, logs_output]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch(theme=theme.get_theme())
