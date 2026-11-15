"""Science questions always use the AI provider; no canned scientific answers."""
from aero_psi.copilot import ask, validate_history


def explain(question):
    return answer_question({}, question, mode='explain')


def answer_question(catalog, question, mode='auto', history=None):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
        raise ValueError('question must be 1–2000 characters')
    if mode not in ('auto', 'evidence', 'explain'):
        raise ValueError('mode must be auto, evidence, or explain')
    history = validate_history(history)
    return ask(catalog, question, allow_background=mode != 'evidence',
               history=history, retrieve_sources=mode != 'explain')
