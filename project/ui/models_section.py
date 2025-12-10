import gradio as gr
from core.provider import Provider, ModelConfig

def render():
    with gr.Accordion("3. Models Configuration", open=True):
        with gr.Row():
            alias_input = gr.Textbox(label="Alias (e.g. gpt-4o)", placeholder="gpt-4o")
            provider_input = gr.Dropdown(choices=[p.value for p in Provider], label="Provider", value="OpenAI")
            model_name_input = gr.Textbox(label="Model Name", placeholder="gpt-4o")
        with gr.Row():
            base_url_input = gr.Textbox(label="Base URL", value="https://api.openai.com/v1")
            api_key_input = gr.Textbox(label="API Key", type="password")
        
        add_btn = gr.Button("Add Model")
        
        models_list = gr.Dataframe(
            headers=["Alias", "Provider", "Model Name", "Base URL"],
            datatype=["str", "str", "str", "str"],
            interactive=False,
            label="Configured Models"
        )
        
        with gr.Row():
            delete_dropdown = gr.Dropdown(label="Select Model to Delete", choices=[], interactive=True)
            delete_btn = gr.Button("Delete Selected Model", variant="stop")

        test_btn = gr.Button("Test All Providers")
        
        models_state = gr.State([]) # List of ModelConfig objects

    def add_model(alias, provider, model_name, base_url, api_key, current_models):
        if not alias or not model_name or not base_url or not api_key:
            return current_models, gr.update(), gr.update(), alias, provider, model_name, base_url, api_key
        
        # Remove existing if same alias to allow updates
        updated_models = [m for m in current_models if m.alias != alias]
        
        new_config = ModelConfig(alias, provider, model_name, base_url, api_key)
        updated_models.append(new_config)
        
        # Update dataframe
        df_data = [[m.alias, m.provider, m.model_name, m.base_url] for m in updated_models]
        aliases = [m.alias for m in updated_models]
        
        # Reset inputs
        return updated_models, df_data, gr.update(choices=aliases), "", "OpenAI", "", "https://api.openai.com/v1", ""

    def delete_model(alias_to_delete, current_models):
        if not alias_to_delete:
            return current_models, gr.update(), gr.update()
        
        updated_models = [m for m in current_models if m.alias != alias_to_delete]
        df_data = [[m.alias, m.provider, m.model_name, m.base_url] for m in updated_models]
        aliases = [m.alias for m in updated_models]
        
        return updated_models, df_data, gr.update(choices=aliases, value=None)

    add_btn.click(
        add_model,
        inputs=[alias_input, provider_input, model_name_input, base_url_input, api_key_input, models_state],
        outputs=[models_state, models_list, delete_dropdown, alias_input, provider_input, model_name_input, base_url_input, api_key_input]
    )

    delete_btn.click(
        delete_model,
        inputs=[delete_dropdown, models_state],
        outputs=[models_state, models_list, delete_dropdown]
    )

    return alias_input, provider_input, model_name_input, base_url_input, api_key_input, add_btn, models_list, test_btn, models_state
