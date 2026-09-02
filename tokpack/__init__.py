"""tokpack - a token encoder for LLM inputs.

Like a video codec, but the "viewer" is a language model: a lossless level that
only removes bytes the model gains nothing from, and lossy levels that drop
detail a coding agent rarely needs (repeated log lines, function bodies, comments).
"""
from .pipeline import encode, Result
from .count import count_tokens

__all__ = ["encode", "Result", "count_tokens"]
__version__ = "0.1.0"
