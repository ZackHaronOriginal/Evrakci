"""Processing pipeline: split -> ocr -> classify -> extract -> export.

Pure Python, no Qt imports, so every stage can be tested and reused
(for example by a future command-line or hosted version) without the UI.
"""
