"""Surreal World patch package (repo SSOT: deploy/surreal_world/).

Regular-package marker so the repo copy wins sys.path resolution against a
stale installed copy. See surreal_arch/__init__.py for the namespace-shadowing
failure mode this prevents.
"""
