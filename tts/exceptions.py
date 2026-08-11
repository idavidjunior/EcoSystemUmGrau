"""Exceções do Speech Pipeline."""


class SpeechPipelineError(Exception):
    """Erro base do pipeline de fala."""
    pass


class TextTooShortError(SpeechPipelineError):
    """Texto muito curto para gerar áudio (abaixo de MIN_TEXT_LENGTH)."""
    pass


class TextTooLongError(SpeechPipelineError):
    """Texto excede MAX_TEXT_LENGTH após sanitização."""
    pass


class TTSynthesisError(SpeechPipelineError):
    """Falha na síntese de áudio pelo motor TTS."""
    pass


class ValidationError(SpeechPipelineError):
    """Texto não passou na validação final antes da síntese."""
    pass


class ConfigurationError(SpeechPipelineError):
    """Erro de configuração (voz, path, parâmetros inválidos)."""
    pass


class ContentExtractionError(SpeechPipelineError):
    """Erro durante extração/conversão de conteúdo bloqueado."""
    pass
