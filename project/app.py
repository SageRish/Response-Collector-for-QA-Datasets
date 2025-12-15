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
        execution_mode, collection_scope, start_btn, stop_btn, stop_dropdown, stop_status = collection_section.render()
        
        # 5. Progress
        progress_df = progress_section.render()
        
        # 6. Logs
        logs_output = logs_section.render()

        # --- Logic ---

        # Shared cancellation state
        running_tasks = {}

        def handle_stop(model_alias):
            print(f"DEBUG: Stop requested for {model_alias}")
            if model_alias:
                task = running_tasks.get(model_alias)
                if task and not task.done():
                    task.cancel()
                    return f"🛑 Stopping {model_alias}..."
                return f"⚠️ {model_alias} is not running."
            return "⚠️ Please select a model to stop."
        
        stop_btn.click(
            handle_stop,
            inputs=[stop_dropdown],
            outputs=[stop_status]
        )

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
            execution_mode,
            collection_scope
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

            # Initialize running tasks
            running_tasks.clear()

            # Initialize progress states
            # Map alias -> list representation
            progress_states = {}
            for m in models:
                progress_states[m.alias] = [m.alias, "0.0%", f"0/{dataset_loader.num_questions}", "-", "Pending"]
            
            def get_progress_data():
                return [progress_states[m.alias] for m in models]
            
            # Initial update
            yield {
                progress_df: get_progress_data(), 
                logs_output: logger.get_logs(),
                stop_dropdown: gr.update(choices=[m.alias for m in models], value=None, interactive=True),
                stop_status: ""
            }

            def progress_callback(state):
                progress_states[state.model_alias] = state.to_list()

            async def run_model_task(model):
                # Register task
                running_tasks[model.alias] = asyncio.current_task()
                
                try:
                    data, missing = await collect_responses(
                        model, dataset_loader, 
                        int(short_tokens), int(long_tokens), 
                        system_prompt, logger, progress_callback,
                        collection_scope=collection_scope
                    )
                    
                    # Save outputs
                    output_dir = "outputs"
                    save_json(format_dataset_output(model.alias, data), os.path.join(output_dir, f"{model.alias}_dataset.json"))
                    save_json(missing, os.path.join(output_dir, f"{model.alias}_missing_responses.json"))
                
                except asyncio.CancelledError:
                    # Handled in collector.py but re-raised or returned?
                    # If collector.py catches and returns, we won't get here via exception.
                    # But if we are waiting on collect_responses and it gets cancelled, 
                    # collector.py catches it and returns data.
                    # So we might not need this except block if collector.py swallows it.
                    # Let's check collector.py again.
                    # It catches CancelledError and returns (data, missing).
                    # So this block is actually unreachable if collector.py handles it perfectly.
                    # BUT, if the cancellation happens before collect_responses starts (unlikely) or inside save_json?
                    # Safe to keep generic exception handler.
                    pass

                except Exception as e:
                    logger.log(f"[{model.alias}] Critical failure: {str(e)}")
                    # Update status to failed
                    current = progress_states[model.alias]
                    current[-1] = "Failed"
                    progress_states[model.alias] = current
                
                finally:
                    # Cleanup
                    if model.alias in running_tasks:
                        del running_tasks[model.alias]

            if execution_mode == "Sequential":
                for model in models:
                    task = asyncio.create_task(run_model_task(model))
                    running_tasks[model.alias] = task # Redundant but safe
                    
                    try:
                        while not task.done():
                            yield {progress_df: get_progress_data(), logs_output: logger.get_logs()}
                            await asyncio.sleep(0.5)
                        await task
                    except asyncio.CancelledError:
                        # If the main loop is cancelled? Unlikely.
                        pass
            else:
                # Parallel
                # Check for unique providers
                providers = [m.provider for m in models]
                if len(providers) != len(set(providers)):
                    logger.log("Warning: Parallel mode selected but providers are not unique. Rate limits may occur.")
                
                tasks = []
                for m in models:
                    t = asyncio.create_task(run_model_task(m))
                    tasks.append(t)
                    running_tasks[m.alias] = t

                while not all(t.done() for t in tasks):
                    yield {progress_df: get_progress_data(), logs_output: logger.get_logs()}
                    await asyncio.sleep(0.5)
                
                # Await all to ensure exceptions are propagated/handled
                for t in tasks:
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass

            logger.log("All collections finished.")
            yield {
                progress_df: get_progress_data(), 
                logs_output: logger.get_logs(),
                stop_dropdown: gr.update(choices=[], value=None, interactive=False),
                stop_status: "Collection finished."
            }

        start_btn.click(
            run_collection,
            inputs=[
                short_tokens, long_tokens, system_prompt,
                dataset_state, models_state, execution_mode,
                collection_scope
            ],
            outputs=[progress_df, logs_output, stop_dropdown, stop_status]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch(theme=theme.get_theme())
