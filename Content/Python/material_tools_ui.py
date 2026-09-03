"""Legacy menu-callable wrappers.

The live menu now routes through `envui` (command registry + organized sections).
These wrappers remain so any older menu entries or scripts still work.
"""

from __future__ import annotations

from envui import commands


def capture_thumbnails() -> None:
    commands.run("materials.capture_thumbnails")


def run_disk_audits() -> None:
    commands.run("materials.run_audits")


def capture_and_audit() -> None:
    commands.run("materials.capture_and_audit")


def print_output_paths() -> None:
    commands.run("materials.print_paths")


def open_modifier_panel() -> None:
    commands.run("modifiers.open_panel")

