"""Application adapters; the reasoning engine remains independent of HTTP."""

from .http import create_server

__all__ = ["create_server"]
