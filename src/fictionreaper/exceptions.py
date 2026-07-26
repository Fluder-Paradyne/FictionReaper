"""Domain exceptions for FictionReaper."""

from __future__ import annotations


class FictionReaperError(Exception):
    """Base error for FictionReaper."""


class InvalidURLError(FictionReaperError, ValueError):
    """Raised when a URL is not a supported Royal Road fiction or chapter URL."""


class FetchError(FictionReaperError):
    """Raised when an HTTP request fails."""


class ParseError(FictionReaperError):
    """Raised when page HTML cannot be parsed into expected models."""
