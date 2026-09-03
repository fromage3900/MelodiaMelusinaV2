"""Battle Test Harness GUI — tkinter window for driving Melodia encounters.

Launches a standalone window with full battle controls:
  - Enemy spawn dropdown
  - Player/enemy HP bars, phase, combo
  - Command buttons (Basic Attack, Skill, Ultimate, Defend, Flee)
  - Grade selector for rhythm resolution
  - Battle log viewer
  - Victory/Defeat notification

Usage:
    from gmm.ui.battle_gui import launch_battle_gui
    launch_battle_gui()

Or standalone:
    python -m gmm.ui.battle_gui
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from gmm.melodia.enemies import list_enemies, DEMO_ENEMIES
from gmm.melodia.skills import list_skills, DEMO_SKILLS
from gmm.melodia.battle import BattleTestHarness


# ---------------------------------------------------------------------------
# Color palette (Figma Game UI → tkinter hex)
# ---------------------------------------------------------------------------

def _to_hex(rgba: tuple[float, float, float, float]) -> str:
    r = int(rgba[0] * 255)
    g = int(rgba[1] * 255)
    b = int(rgba[2] * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


class GUColors:
    VOID = _to_hex((0.051, 0.071, 0.141, 1.0))
    SURFACE = _to_hex((0.071, 0.094, 0.165, 0.92))
    SURFACE_LIGHT = _to_hex((0.102, 0.122, 0.227, 0.85))
    GOLD = _to_hex((1.0, 0.902, 0.4, 1.0))
    CYAN = _to_hex((0.4, 0.851, 1.0, 1.0))
    PEARL = _to_hex((0.941, 0.863, 0.941, 1.0))
    MAGENTA = _to_hex((1.0, 0.431, 0.698, 1.0))
    TEXT_PRIMARY = _to_hex((0.925, 0.918, 0.957, 1.0))
    TEXT_SECONDARY = _to_hex((0.663, 0.655, 0.753, 1.0))
    TEXT_MUTED = _to_hex((0.431, 0.376, 0.502, 1.0))
    HP = _to_hex((0.4, 0.851, 1.0, 1.0))
    SP = _to_hex((1.0, 0.902, 0.4, 1.0))
    ULT = _to_hex((1.0, 0.431, 0.698, 1.0))
    RED = "#ff4466"
    GREEN = "#44ff88"
    BG = "#0a0e1a"
    SURF = "#121a30"


GRADE_COLORS = {
    "perfect": GUColors.GOLD,
    "great": GUColors.CYAN,
    "good": GUColors.PEARL,
    "miss": GUColors.MAGENTA,
}

GRADE_LABELS = {
    "perfect": "PERFECT",
    "great": "GREAT",
    "good": "GOOD",
    "miss": "MISS",
}

COMMAND_LABELS = {
    "basic_attack": "Basic Attack",
    "skill": "Skill",
    "ultimate": "Ultimate",
    "defend": "Defend",
    "flee": "Flee",
}


class BattleGUI:
    """Tkinter battle test harness window."""

    def __init__(self, master: tk.Tk):
        self.master = master
        self.harness = BattleTestHarness()
        self._build_ui()
        self._update_state()

    def _build_ui(self):
        m = self.master
        m.title("Melodia Battle Test Harness")
        m.configure(bg=GUColors.VOID)
        m.minsize(680, 580)

        style = ttk.Style()
        style.theme_use("clam")

        # -- Top frame: enemy selector + spawn --
        top = tk.Frame(m, bg=GUColors.SURFACE, pady=6, padx=8)
        top.pack(fill=tk.X)

        tk.Label(top, text="Enemy:", fg=GUColors.TEXT_MUTED, bg=GUColors.SURFACE,
                 font=("IBM Plex Mono", 9)).pack(side=tk.LEFT, padx=(0, 6))

        self.enemy_var = tk.StringVar()
        enemy_names = list(DEMO_ENEMIES.keys())
        self.enemy_menu = ttk.Combobox(top, textvariable=self.enemy_var,
                                       values=enemy_names, state="readonly", width=18)
        self.enemy_menu.pack(side=tk.LEFT, padx=(0, 8))
        if enemy_names:
            self.enemy_var.set(enemy_names[0])

        self.spawn_btn = tk.Button(top, text="Spawn Encounter",
                                   bg=GUColors.GOLD, fg=GUColors.VOID,
                                   font=("Inter", 10, "bold"),
                                   command=self._on_spawn)
        self.spawn_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.phase_label = tk.Label(top, text="Phase: None", fg=GUColors.CYAN,
                                    bg=GUColors.SURFACE, font=("IBM Plex Mono", 9))
        self.phase_label.pack(side=tk.RIGHT, padx=(4, 0))

        self.turn_label = tk.Label(top, text="Turn: 0", fg=GUColors.TEXT_SECONDARY,
                                   bg=GUColors.SURFACE, font=("IBM Plex Mono", 9))
        self.turn_label.pack(side=tk.RIGHT, padx=(8, 4))

        # -- Main content area: player | enemy --
        main = tk.Frame(m, bg=GUColors.VOID, padx=8, pady=6)
        main.pack(fill=tk.BOTH, expand=True)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        self._build_player_panel(main)
        self._build_enemy_panel(main)

        # -- Combo + Grades --
        stats = tk.Frame(m, bg=GUColors.SURFACE, pady=4, padx=8)
        stats.pack(fill=tk.X)

        self.combo_label = tk.Label(stats, text="COMBO x 0", fg=GUColors.GOLD,
                                    bg=GUColors.SURFACE, font=("Fraunces", 14))
        self.combo_label.pack(side=tk.LEFT, padx=(0, 20))

        self.grades_label = tk.Label(stats, text="P:0  G:0  G:0  M:0",
                                     fg=GUColors.TEXT_SECONDARY, bg=GUColors.SURFACE,
                                     font=("IBM Plex Mono", 9))
        self.grades_label.pack(side=tk.LEFT)

        # -- Command buttons --
        cmd_frame = tk.Frame(m, bg=GUColors.SURF, pady=6, padx=8)
        cmd_frame.pack(fill=tk.X)

        for cmd_key in ("basic_attack", "skill", "ultimate", "defend", "flee"):
            label = COMMAND_LABELS[cmd_key]
            btn = tk.Button(cmd_frame, text=label,
                            bg=GUColors.SURFACE_LIGHT, fg=GUColors.TEXT_PRIMARY,
                            font=("Inter", 9),
                            command=lambda c=cmd_key: self._on_command(c))
            btn.pack(side=tk.LEFT, padx=3)

        # -- Skill selector (for skill command) --
        skill_frame = tk.Frame(m, bg=GUColors.SURF, pady=2, padx=8)
        skill_frame.pack(fill=tk.X)

        tk.Label(skill_frame, text="Skill:", fg=GUColors.TEXT_MUTED,
                 bg=GUColors.SURF, font=("IBM Plex Mono", 9)).pack(side=tk.LEFT, padx=(0, 4))

        self.skill_var = tk.StringVar()
        skill_names = [s.skill_id for s in DEMO_SKILLS]
        self.skill_menu = ttk.Combobox(skill_frame, textvariable=self.skill_var,
                                        values=skill_names, state="readonly", width=22)
        self.skill_menu.pack(side=tk.LEFT, padx=(0, 12))
        if skill_names:
            self.skill_var.set(skill_names[0])

        # -- Grade selector + execute --
        tk.Label(skill_frame, text="Grade:", fg=GUColors.TEXT_MUTED,
                 bg=GUColors.SURF, font=("IBM Plex Mono", 9)).pack(side=tk.LEFT, padx=(0, 4))

        self.grade_var = tk.StringVar(value="perfect")
        grade_menu = ttk.Combobox(skill_frame, textvariable=self.grade_var,
                                   values=["perfect", "great", "good", "miss"],
                                   state="readonly", width=10)
        grade_menu.pack(side=tk.LEFT, padx=(0, 8))

        self.execute_btn = tk.Button(skill_frame, text="Execute Turn",
                                     bg=GUColors.CYAN, fg=GUColors.VOID,
                                     font=("Inter", 10, "bold"),
                                     command=self._on_execute)
        self.execute_btn.pack(side=tk.LEFT)

        # -- Battle log --
        log_frame = tk.Frame(m, bg=GUColors.VOID, padx=8, pady=2)
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="Battle Log", fg=GUColors.TEXT_MUTED,
                 bg=GUColors.VOID, font=("IBM Plex Mono", 8)).pack(anchor=tk.W)

        self.log_text = tk.Text(log_frame, height=6, bg=GUColors.BG,
                                fg=GUColors.TEXT_SECONDARY,
                                font=("Consolas", 9), bd=0,
                                highlightbackground=GUColors.SURFACE,
                                highlightcolor=GUColors.GOLD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(self.log_text, command=self.log_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scroll.set)

    def _build_player_panel(self, parent):
        frame = tk.LabelFrame(parent, text=" Player ", fg=GUColors.CYAN,
                              bg=GUColors.SURF, font=("IBM Plex Mono", 9),
                              padx=8, pady=6)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.player_hp_bar = self._make_bar(frame, "HP", GUColors.HP, 0.75)
        self.player_sp_bar = self._make_bar(frame, "SP", GUColors.SP, 0.5)
        self.player_ult_bar = self._make_bar(frame, "ULT", GUColors.ULT, 0.0)

        self.player_hp_text = tk.Label(frame, text="100 / 100",
                                       fg=GUColors.TEXT_PRIMARY, bg=GUColors.SURF,
                                       font=("IBM Plex Mono", 9))
        self.player_hp_text.pack(anchor=tk.W)

    def _build_enemy_panel(self, parent):
        frame = tk.LabelFrame(parent, text=" Enemy ", fg=GUColors.MAGENTA,
                              bg=GUColors.SURF, font=("IBM Plex Mono", 9),
                              padx=8, pady=6)
        frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        self.enemy_name_label = tk.Label(frame, text="—",
                                         fg=GUColors.PEARL, bg=GUColors.SURF,
                                         font=("Fraunces", 14))
        self.enemy_name_label.pack(anchor=tk.W)

        self.enemy_hp_bar = self._make_bar(frame, "HP", GUColors.HP, 1.0)
        self.enemy_hp_text = tk.Label(frame, text="",
                                      fg=GUColors.TEXT_PRIMARY, bg=GUColors.SURF,
                                      font=("IBM Plex Mono", 9))
        self.enemy_hp_text.pack(anchor=tk.W)

        self.enemy_tough_bar = self._make_bar(frame, "Tough", GUColors.CYAN, 1.0)
        self.enemy_tough_text = tk.Label(frame, text="",
                                         fg=GUColors.TEXT_SECONDARY, bg=GUColors.SURF,
                                         font=("IBM Plex Mono", 9))
        self.enemy_tough_text.pack(anchor=tk.W)

        self.enemy_meta = tk.Label(frame, text="", fg=GUColors.TEXT_MUTED,
                                   bg=GUColors.SURF, font=("IBM Plex Mono", 9))
        self.enemy_meta.pack(anchor=tk.W, pady=(4, 0))

    def _make_bar(self, parent, label_text, color_hex, initial=0.0):
        row = tk.Frame(parent, bg=GUColors.SURF)
        row.pack(fill=tk.X, pady=2)

        tk.Label(row, text=label_text, width=4, anchor=tk.W,
                 fg=color_hex, bg=GUColors.SURF,
                 font=("IBM Plex Mono", 8)).pack(side=tk.LEFT)

        canvas = tk.Canvas(row, height=12, bg=GUColors.BG,
                           highlightthickness=0, bd=0)
        canvas.pack(fill=tk.X, expand=True, padx=(4, 0))

        w = 10
        fill_id = canvas.create_rectangle(0, 0, int(w * initial), 12,
                                          fill=color_hex, outline="")
        canvas.update()
        cw = canvas.winfo_width() or 200
        canvas.coords(fill_id, 0, 0, int(cw * initial), 12)

        def _on_resize(ev, c=canvas, fid=fill_id, init=initial):
            c.coords(fid, 0, 0, int(ev.width * init), 12)

        canvas.bind("<Configure>", _on_resize)
        return (canvas, fill_id)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _log(self, msg: str, color: str = ""):
        tag = f"color_{len(self.log_text.dump(1.0, tk.END))}"
        self.log_text.insert(tk.END, f"> {msg}\n", tag)
        if color:
            self.log_text.tag_config(tag, foreground=color)
        self.log_text.see(tk.END)

    def _update_bars(self, canvas, fill_id, ratio):
        cw = canvas.winfo_width() or 200
        r = max(0.0, min(ratio, 1.0))
        canvas.coords(fill_id, 0, 0, int(cw * r), 12)

    def _on_spawn(self):
        enemy_id = self.enemy_var.get()
        result = self.harness.spawn_encounter(enemy_id)
        if result.get("ok"):
            self._log(f"Encounter started: {result['enemy']['display_name']} "
                      f"({result['enemy']['element']}, BPM {result['enemy']['bpm']})",
                      GUColors.GREEN)
        else:
            self._log(f"ERROR: {result.get('error', 'spawn failed')}", GUColors.RED)
            messagebox.showerror("Spawn Error", result.get("error", ""))
        self._update_state()

    def _on_command(self, command: str):
        if self.harness.phase == "EnemyTurn":
            self._log("Enemy must attack first — click Execute Turn", GUColors.GOLD)
            return
        if self.harness.phase == "Victory":
            self._log("Encounter already won — spawn a new one", GUColors.GOLD)
            return
        if self.harness.phase == "Defeat":
            self._log("Defeated — spawn a new encounter", GUColors.GOLD)
            return
        if self.harness.phase == "Fled":
            self._log("Already fled — spawn a new encounter", GUColors.GOLD)
            return

        if command == "flee":
            result = self.harness.flee()
            if result.get("ok"):
                self._log("Fled from battle!", GUColors.GOLD)
                self._update_state()
            return

        skill_id = self.skill_var.get() if command == "skill" else ""

        if command == "skill":
            result = self.harness.issue_command(command, skill_id)
        else:
            result = self.harness.issue_command(command)

        if result.get("ok"):
            label = COMMAND_LABELS[command]
            skill_txt = f" ({skill_id})" if skill_id else ""
            self._log(f"Issued {label}{skill_txt} — resolving rhythm...", GUColors.TEXT_PRIMARY)
        else:
            self._log(f"Command failed: {result.get('error', '')}", GUColors.RED)
            if self.harness.phase == "AwaitingPlayerCommand":
                self._log("Waiting for player command...", GUColors.CYAN)

        self._update_state()

    def _on_execute(self):
        phase = self.harness.phase

        if phase == "EnemyTurn":
            result = self.harness.enemy_attack()
            if result.get("ok"):
                color = GUColors.MAGENTA if result["phase"] == "Defeat" else GUColors.PEARL
                self._log(f"Enemy attacks for {result['damage']:.0f} damage. "
                          f"Player HP: {result['player_hp']:.0f}", color)
                if result["phase"] == "Defeat":
                    self._log("DEFEAT! You have fallen.", GUColors.RED)
                    messagebox.showinfo("Defeat", "You have been defeated in battle.")
            else:
                self._log(f"Enemy attack failed: {result.get('error', '')}", GUColors.RED)
            self._update_state()
            return

        if phase == "RhythmExecution":
            grade = self.grade_var.get()
            result = self.harness.resolve_rhythm(grade)
            if result.get("ok"):
                color = GRADE_COLORS.get(grade, GUColors.TEXT_PRIMARY)
                grade_label = GRADE_LABELS.get(grade, grade)
                dmg = result["damage"]
                self._log(f"Resolved: {grade_label} — Damage: {dmg:.0f}, "
                          f"Combo: {result['combo']}", color)
                if result["phase"] == "Victory":
                    self._log("VICTORY! Encounter won!", GUColors.GOLD)
                    messagebox.showinfo("Victory", "You have won the battle!")
                elif result["phase"] == "EnemyTurn":
                    self._log("Enemy turn — click Execute Turn again to process enemy attack",
                              GUColors.CYAN)
                self._update_state()
            return

        if phase == "Victory":
            self.harness.end_encounter()
            self._log("Encounter ended. Spawn a new one to continue.", GUColors.GREEN)
            self._update_state()
            return

        self._log(f"Cannot execute in phase '{phase}'", GUColors.GOLD)

    def _update_state(self):
        state = self.harness.poll_state()
        phase = state["phase"]
        player = state["player"]
        enemy = state["enemy"]

        self.phase_label.config(text=f"Phase: {phase}")
        self.turn_label.config(text=f"Turn: {state['turn']}")
        self.combo_label.config(text=f"COMBO x {state['combo']}")

        g = state["grades"]
        self.grades_label.config(
            text=f"P:{g['perfect']}  G:{g['great']}  G:{g['good']}  M:{g['miss']}")

        if player:
            hp_r = player["hp"] / player["max_hp"] if player["max_hp"] else 0
            sp_r = player["sp"] / player["max_sp"] if player["max_sp"] else 0
            ult_r = player["ult"] / player["max_ult"] if player["max_ult"] else 0
            self._update_bars(self.player_hp_bar[0], self.player_hp_bar[1], hp_r)
            self._update_bars(self.player_sp_bar[0], self.player_sp_bar[1], sp_r)
            self._update_bars(self.player_ult_bar[0], self.player_ult_bar[1], ult_r)
            self.player_hp_text.config(
                text=f"{player['hp']:.0f} / {player['max_hp']:.0f}")

        if enemy:
            self.enemy_name_label.config(text=enemy["name"])
            e_hp_r = enemy["hp"] / enemy["max_hp"] if enemy["max_hp"] else 0
            e_tough_r = enemy["toughness"] / enemy["max_toughness"] if enemy["max_toughness"] else 0
            self._update_bars(self.enemy_hp_bar[0], self.enemy_hp_bar[1], e_hp_r)
            self._update_bars(self.enemy_tough_bar[0], self.enemy_tough_bar[1], e_tough_r)
            self.enemy_hp_text.config(text=f"{enemy['hp']:.0f} / {enemy['max_hp']:.0f}")
            self.enemy_tough_text.config(
                text=f"Toughness: {enemy['toughness']:.0f} / {enemy['max_toughness']:.0f}")
            self.enemy_meta.config(
                text=f"Element: {enemy['element']}  BPM: {enemy['bpm']}")
        else:
            self.enemy_name_label.config(text="—")
            self.enemy_hp_text.config(text="")
            self.enemy_tough_text.config(text="")
            self.enemy_meta.config(text="")

        if phase == "Victory":
            self.spawn_btn.config(bg=GUColors.GREEN)
        elif phase == "Defeat":
            self.spawn_btn.config(bg=GUColors.RED)
        else:
            self.spawn_btn.config(bg=GUColors.GOLD)

    def run(self):
        self._log("Battle Test Harness ready — select an enemy and spawn.", GUColors.GREEN)
        self.master.mainloop()


def launch_battle_gui():
    """Launch the Battle Test Harness GUI in a new tkinter window (blocking)."""
    root = tk.Tk()
    root.geometry("700x620")
    app = BattleGUI(root)
    app.run()
    return app


def launch_battle_gui_nonblocking():
    """Launch the GUI without blocking the caller (uses after() loop).

    Suitable for calling from UE Python console or EnvUI menu.
    """
    root = tk.Tk()
    root.geometry("700x620")
    app = BattleGUI(root)
    app._log("Battle Test Harness ready (non-blocking mode)", GUColors.GREEN)

    def _poll():
        try:
            root.update_idletasks()
            root.update()
            root.after(50, _poll)
        except tk.TclError:
            pass

    root.after(50, _poll)
    return app


def close_battle_gui(app: Optional[BattleGUI] = None):
    """Close the battle GUI window."""
    if app:
        try:
            app.master.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    launch_battle_gui()
