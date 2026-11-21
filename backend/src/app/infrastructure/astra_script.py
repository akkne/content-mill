from app.infrastructure.codex_script import CodexCli


class AstraCli(CodexCli):
    model_id = "gpt-6.2-astra"
    model = "codex:" + model_id
    config_args = ("-c", 'model_reasoning_effort="high"')
