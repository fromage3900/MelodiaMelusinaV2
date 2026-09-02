"""Surreal Architecture overhaul package (repo SSOT: deploy/surreal_arch/).

This __init__.py makes the repo copy a REGULAR package so it wins sys.path
resolution against a stale installed copy in Blender's addons directory.
Without it, Python treats this directory as a namespace package and a regular
package of the same name anywhere later on sys.path (e.g. the AppData install)
silently shadows it - which is how the 2026-08-29 "lost panel" drift happened.
"""
