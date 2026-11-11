#!/usr/bin/env python3
"""Backward-compatible alias for tools/build_blogs.py."""
try:
    from .build_blogs import main
except ImportError:  # direct execution: python tools/sync_blogs.py
    from build_blogs import main

if __name__ == "__main__":
    main()
