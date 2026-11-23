from app.infrastructure.providers.text.codex_script import CodexCli


class SolCli(CodexCli):
    model_id = "gpt-6.2-sol"
    model = "codex:" + model_id
    config_args = ("-c", 'model_reasoning_effort="high"')
