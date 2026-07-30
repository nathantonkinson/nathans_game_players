"""
UniWar Game Visualizer
======================
A tkinter-based visualizer for UniWar game states.
Written by replit after looking at github commit 854f41d5ce41498fe9468fa8b031cef1cffd8fc3

Usage (from the UniWar/ directory):
    python visualizer.py                     # loads maps/plainsLine.yaml
    python visualizer.py maps/mymap.yaml     # loads a specific map

You can also import and use it programmatically:
    from visualizer import Visualizer
    from src.loader import Loader
    from src.engine.engine import Engine

    loader = Loader()
    gamedata = loader.load_gameData()
    gamestate = loader.load_map("plainsLine.yaml")
    engine = Engine(gamestate, gamedata)

    viz = Visualizer(gamedata, gamestate, engine)
    viz.run()

    # To push a new state into the running visualizer from outside:
    viz.update_state(new_gamestate)
"""

import sys
import os
import math
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import replace

# Make sure the UniWar package root is on the path, regardless of where
# the script is launched from.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from src.data.gameDataClasses import GameData, GameState, clsAction, clsLoc
from src.engine.engine import Engine
import src.data.generated_constants as gc

#region constants

HEX_SIZE    = 72          # pixel "radius" of each hex
MARGIN      = HEX_SIZE + 10
INFO_WIDTH  = 290         # right panel width in pixels

# Player colours: index 1 = player 1, etc.
PLAYER_COLORS    = ["#ffffff", "#3498db", "#cc2e2e", "#12c912", "#9b59b6"]
PLAYER_NAMES     = ["error player 0", "Player 1", "Player 2", "Player 3", "Player 4"]

# Terrain number → display colour
TERRAIN_COLORS = {
    1:  "#90c060",  # Plain, light green
    2:  "#5f9ea0",  # Harbor, grey blue I guess? OR should we do BORDER?
    3:  "#483f3f",  # Mountain, dark grey
    4:  "#336633",  # Forest, dark green
    5:  "#9b5555",  # Medical, mild red
    6:  "#627D66",  # Road, greenish grey
    7:  "#504e73",  # Bridge, bluish grey
    8:  "#e0c070",  # Desert
    9:  "#5a7a30",  # Swampm sickly green
    10: "#b0b0b8",  # City, idk grey
    11: "#24A1A1",  # Reef, teal? or we could do a pink?
    12: "#555560",  # Chasm
    13: "#2277ee",  # Waterm light blue
    14: "#0a0a99",  # Ocean, dark blue
    15: "#e08020",  # Base, ugh another grey?
    16: "#111111",  # Void, black
}
DARKNESS_THRESHOLD = 0.5 # Terrain indexes with dark colours, so poor contrast against dark text, so use white text instead

MOVED_COLOR = "#f0c030"
TARGET_COLOR =  "#e03030" 

def color_darkness(hex_color: str) -> float:
    #inputs string color like "#24A1A1" and outputs a darkness number from 0 (white) to 1 (black)
    # Remove '#'
    hex_color = hex_color.lstrip('#')

    # Convert to 0–1 RGB
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255

    # WCAG luminance
    L = 0.2126*r + 0.7152*g + 0.0722*b

    # Threshold ~0.5 works well
    return L

def write_colors_to_file():
    #write the TERRAIN_COLORS into the terrains csv
    pass

#endregion constants

#region hex geomeetry helpers

def hex_center(h: int, w: int) -> tuple[float, float]:
    """
    Convert grid (row=h, col=w) to canvas pixel centre.

    UniWar adjacency rule:  prev-row same+col-1 | same-row col±1 | next-row same+col+1
    This is an "odd-r" offset grid: odd rows shift right by half a hex.
    We use pointy-top hexagons.
    """
    hw = HEX_SIZE * math.sqrt(3)        # hex width  (flat edge to flat edge)
    x = w * hw + (h % 2) * hw / 2 + MARGIN
    y = h * HEX_SIZE * 1.5             + MARGIN
    return x, y


def hex_corners(cx: float, cy: float, size: float) -> list[float]:
    """Return flat list of (x, y, x, y …) for the 6 corners of a pointy-top hex."""
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.extend([cx + size * math.cos(angle),
                    cy + size * math.sin(angle)])
    return pts


def pixel_to_hex(px: float, py: float, map_h: int, map_w: int):
    """
    Find the closest hex to pixel (px, py).
    Returns (h, w) or None if nothing is close enough.
    """
    best, best_dist = None, float("inf")
    for h in range(map_h):
        for w in range(map_w):
            cx, cy = hex_center(h, w)
            d = math.hypot(px - cx, py - cy)
            if d < best_dist:
                best_dist, best = d, (h, w)
    return best if best_dist < HEX_SIZE else None

#endregion hex geometry helpers



class Visualizer:
    """
    Interactive hex-grid visualizer for a UniWar GameState.

    Parameters
    ----------
    gamedata  : GameData   – static rules/tables (passed in, not modified)
    gamestate : GameState  – current board state (updated via update_state())
    engine    : Engine     – optional; needed for Pass Turn and action dispatch
    """

    def __init__(self, gamedata: GameData, gamestate: GameState, engine: Engine = None):
        self.gamedata  = gamedata
        self.gamestate = gamestate
        self.engine    = engine

        # Build quick lookup tables from gamedata
        self.unit_by_num  = {u: unit[gc.NAME] for u, unit in enumerate(gamedata.Units_Name)}
        self.terr_by_num  = {t: terrain[gc.NAME] for t, terrain in enumerate(gamedata.Terrains_Name)}
        self.race_by_num  = {r: race[gc.NAME] for r, race in enumerate(gamedata.Races_Name)}

        # Interaction state
        self._selected: tuple | None = None   # (h, w) of selected hex
        self._mode = "idle"                   # "idle" | "unit_selected" | "awaiting_attack" | "awaiting_final_move" (for MoveAfterAttack)
        self.unit_idx: int
        self._highlights: dict[tuple, str] = {} #highlights for mid-move stuff. (h, w) = color
        self._action = {} #with same fields as clsAction, but as dict since immutable
        self._ghost_pos: tuple | None = None #used for ghost of unit mid-move

        self._build_ui()

    # ── UI construction (one time) ───────────────────────────────────────────────────

    def _build_ui(self):
        self.root = tk.Tk()
        self.root.geometry("1300x700")
        self.root.title("UniWar Visualizer")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        # ── Left: scrollable hex canvas ──────────────────────────────────
        left = tk.Frame(self.root, bg="#1e1e2e")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(left, bg="#0d0d1a", cursor="crosshair",
                                highlightthickness=0)
        hbar = tk.Scrollbar(left, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = tk.Scrollbar(left, orient=tk.VERTICAL,   command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        vbar.pack(side=tk.RIGHT,  fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<MouseWheel>", self._on_scroll)     # Windows / macOS
        self.canvas.bind("<Button-4>",  self._on_scroll)     # Linux scroll up
        self.canvas.bind("<Button-5>",  self._on_scroll)     # Linux scroll down

        # ── Right: info panel ────────────────────────────────────────────
        right = tk.Frame(self.root, bg="#18182a", width=INFO_WIDTH, relief=tk.RIDGE, bd=1)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        self._build_info_panel(right)

        # Initial draw
        self._redraw()
        self._update_status()

    def _build_info_panel(self, parent):
        pad = {"padx": 10, "pady": 4}

        # ── Game status ──────────────────────────────────────────────────
        self._label(parent, "GAME STATUS", header=True).pack(anchor="w", **pad)

        self.var_status = tk.StringVar()
        tk.Label(parent, textvariable=self.var_status,
                 fg="#d0d0e0", bg="#18182a", font=("Courier", 9),
                 justify=tk.LEFT, wraplength=INFO_WIDTH - 20
                 ).pack(anchor="w", **pad)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=6, pady=2)

        # ── Selected hex ─────────────────────────────────────────────────
        self._label(parent, "SELECTED HEX", header=True).pack(anchor="w", **pad)

        self.box_hex = self._textbox(parent, height=6)
        self.box_hex.pack(fill=tk.X, padx=10, pady=2)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=6, pady=2)

        # ── Unit details ─────────────────────────────────────────────────
        self._label(parent, "UNIT DETAILS", header=True).pack(anchor="w", **pad)

        self.box_unit = self._textbox(parent, height=12)
        self.box_unit.pack(fill=tk.X, padx=10, pady=2)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=6, pady=2)

        # ── Actions ──────────────────────────────────────────────────────
        self._label(parent, "ACTIONS", header=True).pack(anchor="w", **pad)

        self.var_action_hint = tk.StringVar(value="Click a hex to inspect it.")
        tk.Label(parent, textvariable=self.var_action_hint,
                 fg="#9090b0", bg="#18182a", font=("Courier", 8),
                 justify=tk.LEFT, wraplength=INFO_WIDTH - 20
                 ).pack(anchor="w", padx=10, pady=2)

        self.btn_pass = tk.Button(
            parent, text="⏭  Pass Turn",
            command=self._pass_turn,
            bg="#2a2a4a", fg="white", relief=tk.FLAT,
            activebackground="#3a3a6a", activeforeground="white",
            padx=8, pady=4, cursor="hand2", font=("Courier", 9, "bold")
        )
        self.btn_pass.pack(fill=tk.X, padx=10, pady=4)

        # Legend
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=6, pady=4)
        self._label(parent, "LEGEND", header=True).pack(anchor="w", **pad)
        legend_frame = tk.Frame(parent, bg="#18182a")
        legend_frame.pack(fill=tk.X, padx=10, pady=2)
        self._draw_legend(legend_frame)

    # ── Drawing ───────────────────────────────────────────────────────────

    def _redraw(self): #full redraw, maybe needed when units change position or anything, because layering??
        """Full map redraw."""
        self.canvas.delete("all")
        gs = self.gamestate
        H, W = gs.Map.Map.shape

        # Draw terrain hexes
        for h in range(H):
            for w in range(W):
                self._draw_hex(h, w)

        # Draw units on top
        self._draw_all_units()

        # Update scroll region
        hw = HEX_SIZE * math.sqrt(3)
        max_x = W * hw + (H % 2) * hw / 2 + MARGIN * 2
        max_y = H * HEX_SIZE * 1.5 + MARGIN * 2
        self.canvas.configure(scrollregion=(0, 0, max_x + 20, max_y + 20))

    def _draw_hex(self, h: int, w: int):
        terrain_num = int(self.gamestate.Map.Map[h, w])
        fill  = TERRAIN_COLORS.get(terrain_num, "#666666") #the 6s are default I think
        cx, cy = hex_center(h, w)
        
        is_selected = self._selected == (h, w)
        outline       = "#ffffff" if is_selected else "#2a2a3a"
        outline_width = 2        if is_selected else 1

        corners = hex_corners(cx, cy, HEX_SIZE - 1)
        self.canvas.create_polygon(corners, fill=fill, outline=outline,
                                   width=outline_width, tags=f"hex {h}_{w}")

        # Terrain label
        tname = self.gamedata.Terrains_Name[(terrain_num, gc.NAME)]
        text_color = "#ffffff" if color_darkness(fill) < DARKNESS_THRESHOLD else "#111111"
        self.canvas.create_text(cx, cy + HEX_SIZE * 0.6, text=tname[:5],
                                fill=text_color, font=("Courier", 10),
                                tags=f"hex {h}_{w}")

        # Coordinate label (top of hex)
        self.canvas.create_text(cx, cy - HEX_SIZE * 0.6, text=f"{h},{w}",
                                fill=text_color, font=("Courier", 10),
                                tags=f"hex {h}_{w}")

    def _draw_all_units(self):
        self.canvas.delete("unit")
        units = self.gamestate.Units
        if units.UnitHexes is None:
            return

        num_units = len(units.UnitPlayers)
        for i in range(num_units):
            h   = int(units.UnitHexes[i, gc.X])
            w   = int(units.UnitHexes[i, gc.Y])
            s   = int(units.UnitHexes[i, gc.ALT])   # altitude state
            pl  = int(units.UnitPlayers[i])
            un  = int(units.UnitNumbers[i])
            hp  = int(units.UnitHps[i])

            cx, cy = hex_center(h, w)

            # Altitude offset: push underwater/underground units down + make smaller
            r = HEX_SIZE * 0.5
            if s == 2:   # underwater
                cy += HEX_SIZE * 0.15
                r  *= 0.78
            elif s == 3: # underground
                cy += HEX_SIZE * 0.3
                r  *= 0.65

            color = PLAYER_COLORS[pl % len(PLAYER_COLORS)]
            
            # Circle body
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                    fill=color, outline="#ffffff", width=1,
                                    tags="unit")

            # Unit abbreviation (first 3 chars of name)
            un = self.gamestate.Units.UnitNumbers[i]
            abbrev  = self.gamedata.Units_Name[(un, gc.ABBREVIATION)]
            self.canvas.create_text(cx, cy - 3, text=abbrev,
                                    fill="white", font=("Courier", 20, "bold"),
                                    tags="unit")

            # HP below abbrev
            #could do hp color depends on player but meh
            self.canvas.create_text(cx, cy + 15, text=f"{hp}",
                                    fill="white", font=("Courier", 12),
                                    tags="unit")

            # Altitude indicator
            if s == 2:
                self.canvas.create_text(cx + r - 2, cy - r + 2, text="Submerged",
                                        fill="#88ddff", font=("Courier", 7, "bold"),
                                        tags="unit")
            elif s == 3:
                self.canvas.create_text(cx + r - 2, cy - r + 2, text="▼ Underground",
                                        fill="#ffcc44", font=("Courier", 7),
                                        tags="unit")

    # ── Click handling / actions ─────────────────────────────────────────────────

    def _on_escape(self, event=None):
        """ESC cancels any in-progress multi-step action and returns to idle."""
        if self._mode != "idle":
            self._cancel_action()
            self._redraw()
            self._update_status()

    def _on_click(self, event):
        px = self.canvas.canvasx(event.x)
        py = self.canvas.canvasy(event.y)

        H, W = self.gamestate.Map.Map.shape
        clicked = pixel_to_hex(px, py, H, W)
        if clicked is None:
            return

        h, w = clicked

        if self._mode == "idle":
            # Select this hex; if it has a current-player unit, switch to unit_selected
            
            self.unit_idx = self._unit_at(h, w)
            self._selected = (h, w)

            if self.unit_idx is not None:
                cp = int(self.gamestate.MetadataCurrent.CurrentPlayer)
                owner = int(self.gamestate.Units.UnitPlayers[self.unit_idx])
                if owner == cp:
                    self._mode = "unit_selected"
                    self.var_action_hint.set(
                        f"Unit at ({h},{w}) selected.\n"
                        "Click a destination hex to move/act, or click the same hex to deselect."
                    )
                else:
                    self.var_action_hint.set("That unit belongs to another player.")
            else:
                self.var_action_hint.set(f"Hex ({h},{w}) — no unit. Click a hex with your unit to act.")

        elif self._mode == "unit_selected":
            if (h, w) == self._selected:
                #we should actually cycle through unit altitudes... but not right now
                # Deselect
                self._mode = "idle"
                self._selected = None
                self.var_action_hint.set("Deselected. Click a hex to inspect.")
            else:
                # Attempt to dispatch an action
                self._attempt_action(h, w)

        # ── awaiting_attack: click an adjacent enemy or anywhere else ──
        elif self._mode == "awaiting_attack":
            print("Attempted attack def")
            self._on_attack_click(h, w)

        # ── awaiting_final_move: click an empty hex for MoveAfterAttack
        elif self._mode == "awaiting_final_move":
            self._on_final_move_click(h, w)

        self._redraw()
        self._update_status()
        self._update_hex_info(h, w)

        print(self._mode)
        # print(self.gamestate.Units.UnitHexes)
        # print(self.gamestate.Units.UnitHps)
        # print(self.engine.GameState.Units.UnitHexes)
        # print(self.engine.GameState.Units.UnitHps)

    def _attempt_action(self, to_h: int, to_w: int):
        """
        Build an action dict and call engine.applyAction if the engine is present.
        The action format is intentionally flexible so you can expand it later.
        """
        if self.unit_idx is None:
            self.var_action_hint.set("No unit at source — action cancelled.")
            # self._cancel_action()
            return

        #Initialize action
        beforeAttackLoc = clsLoc(to_h, to_w, self.gamestate.Units.UnitHexes[(self.unit_idx, gc.ALT)])
        self._action = {
            "UnitIndex": self.unit_idx
            , "AbilityNumber": None #attack=1, move=24, not doing things like assimilate or capture yet
            , "BeforeAttackLoc": beforeAttackLoc
            , "DefenderUnitIndex": 255 #attack nothing
            , "AfterAttackLoc": beforeAttackLoc
        }
        
        self._ghost_pos = (to_h, to_w)
        self._selected  = (to_h, to_w)

        #find adjacent enemies
        cp = int(self.gamestate.MetadataCurrent.CurrentPlayer)
        un = self.gamestate.Units.UnitNumbers[self.unit_idx]
        a = self.gamestate.Units.UnitHexes[(self.unit_idx, gc.ALT)]
        r_min = self.gamedata.UnitAltitudes[(un, a, gc.ATTACKRANGEMIN)]
        r_max = self.gamedata.UnitAltitudes[(un, a, gc.ATTACKRANGEMAX)]
        candidate_hexes = self.engine.getHexesInRange(to_h, to_w, r_min, r_max)
        self._targeteable_locs = []
        for (ah, aw) in candidate_hexes:
            #not doing altitude checks yet
            idx = self._unit_at(ah, aw)
            locraw = self.gamestate.Units.UnitHexes[idx]
            loc = clsLoc(locraw[gc.X], locraw[gc.Y], locraw[gc.ALT])
            if idx is not None and int(self.gamestate.Units.UnitPlayers[idx]) != cp:
                self._targeteable_locs.append(loc)

        # Build highlights: gold for the move destination, red for attackable enemies
        self._highlights = {(to_h, to_w): MOVED_COLOR}   # gold — where unit moved
        for coords in self._targeteable_locs:
            self._highlights[coords] = TARGET_COLOR       # red  — attackable enemy

        self._mode = "awaiting_attack"

        if self._targeteable_locs:
            self.var_action_hint.set(
                f"Unit moved to ({to_h},{to_w}).\n"
                f"Red hexes show attackable enemies — click one to attack.\n"
                "Click anywhere else to skip the attack and end the action.\n"
                "[ESC to cancel everything]"
            )
        else:
            self.var_action_hint.set(
                f"Unit moved to ({to_h},{to_w}).\n"
                "No adjacent enemies. Click anywhere to end the action.\n"
                "[ESC to cancel]"
            )
        
    def _on_attack_click(self, h: int, w: int):
        """
        Step 2: the user clicked a hex while we're waiting for an attack target.

        If the clicked hex is a red-highlighted enemy, record the attack and
        check for MoveAfterAttack.  Any other hex ends the sequence immediately.
        """

        # if (h, w) in self._highlights and self._highlights[(h, w)] == TARGET_COLOR:
        found_it = False
        for loc in self._targeteable_locs:
            if loc.X == h and loc.Y == w:
                found_it = True
                break

        if found_it:
            # Valid enemy clicked — record the attack
            self._action["AbilityNumber"] = 1 #attack, ignoring infect stuff right now

            attack_idx = self.engine.hexUnits[(loc.X, loc.Y, loc.Altitude)]
            self._action["DefenderUnitIndex"] = attack_idx

            # Check if this unit has MoveAfterAttack (21)
            un = int(self.gamestate.Units.UnitNumbers[self.unit_idx])
            if self.gamedata.UnitAbilities[(un, 21, gc.RECORDEXISTS)] == 1:
                self._mode = "awaiting_final_move"
                self.var_action_hint.set(
                    f"Attacked unit at ({h},{w}).\n"
                    "This unit has Move After Attack — click a cyan hex for its final position,\n"
                    "or click anywhere else to stay in place.\n"
                    "[ESC to cancel]"
                )
            else:
                # No MoveAfterAttack — send the action now
                self._dispatch_action()
        else:
            # Non-enemy click — end sequence with no attack
            self._action["AbilityNumber"] = 24 #just move
            self._dispatch_action()

    def _on_final_move_click(self, h: int, w: int):
        """
        Step 3 (optional): the unit repositions after its attack (MoveAfterAttack).

        A cyan hex is a valid destination; anything else ends the sequence in place.
        """
        self._action["AfterAttackLoc"] = clsLoc(h, w, self._action.BeforeAttackLoc.Altitude)
        self._dispatch_action()

    def _dispatch_action(self):
        """
        Assembles the final action dict from self._action and calls engine.applyAction.
        Resets all multi-step state afterwards.
        """

        sendAction = clsAction(
            self._action["UnitIndex"]
            , self._action["AbilityNumber"]
            , self._action["BeforeAttackLoc"]
            , self._action["DefenderUnitIndex"]
            , self._action["AfterAttackLoc"]
        )

        try:
            self.engine.applyAction(sendAction)
            # self.gamestate = self.engine.gamestate #it should modify the gamestate in place
            self.var_action_hint.set(
                f"Action sent: {self._action}"
            )
        except Exception as exc:
            self.var_action_hint.set(f"Engine error: {exc}")

        self._cancel_action()   # clean up state regardless

    def _cancel_action(self):
        """Reset all multi-step action state and return to idle."""
        self._mode       = "idle"
        self._selected   = None
        self._action     = None
        self._highlights = {}
        self._ghost_pos  = None
        self.var_action_hint.set("Cancelled. Click a hex to inspect.")

    def _pass_turn(self): #separate from unit actions to help the AI I guess??
        try:
            self.engine.passTurn()
            self._mode = "idle"
            self._selected = None
            self._redraw()
            self._update_status()
            self.var_action_hint.set("Turn passed.")
        except Exception as exc:
            self.var_action_hint.set(f"Engine error: {exc}")

    # ── Info panel updates ─────────────────────────────────────────────

    def _update_status(self):
        gs  = self.gamestate
        cp  = int(gs.MetadataCurrent.CurrentPlayer)
        crds = gs.MetadataCurrent.PlayersCredits

        lines = [
            f"UI Status: {self._mode}",
            f"Map:    {gs.MetadataInitial.MapName}",
            f"Active: {PLAYER_NAMES[cp]} (index {cp})",
            "Credits:",
        ]
        for i, c in enumerate(crds):
            # marker = " ◀" if i == cp else ""
            lines.append(f"  P{i+1}: {int(c)}")

        self.var_status.set("\n".join(lines))

    def _update_hex_info(self, h: int, w: int):
        """Populate the Hex and Unit text boxes for the given coordinates."""
        terrain_num  = int(self.gamestate.Map.Map[h, w])
        terrain_name = self.gamedata.Terrains_Name[(terrain_num, gc.NAME)]
        notes        = self.gamedata.Terrains_Name[(terrain_num, gc.NOTES)]

        hex_lines = [
            f"Coords:  ({h}, {w})",
            f"Terrain: {terrain_name}  (#{terrain_num})",
            f"Notes:   {notes}",
        ]
        self._set_text(self.box_hex, "\n".join(hex_lines))

        unit_idx = self._unit_at(h, w)
        if unit_idx is not None:
            units  = self.gamestate.Units
            pl     = int(units.UnitPlayers[unit_idx])
            un     = int(units.UnitNumbers[unit_idx])
            hp     = int(units.UnitHps[unit_idx])
            a      = int(units.UnitHexes[unit_idx, gc.ALT])
            unitnotes = self.gamedata.Units_Name[(un, gc.NOTES)]
            unitname = self.gamedata.Units_Name[(un, gc.NAME)]
            unittypenum = self.gamedata.Units[(un, gc.UNITTYPENUMBER)]
            unittypename = self.gamedata.Unittypes_Name[(unittypenum, gc.NAME)]
            racenum = self.gamedata.Units[(un, gc.RACENUMBER)]
            racename = self.gamedata.Races_Name[(racenum, gc.NAME)]

            ulines = [
                f"Unit Idx: {unit_idx}",
                f"Owner:    {PLAYER_NAMES[pl]} (#{pl})",
                f"Unit:     {unitname}  (#{un})",
                # f"Race:     {racename}",
                f"HP:       {hp}",
                f"Altitude: {self.gamedata.Altitudes_Name[a, gc.NAME]}",
                # f"Type:     {unittypename}",
                f"Cost:     {self.gamedata.Units[(un, gc.COST)]}",
                # f"Repair:   {self.gamedata.Units[(un, gc.REPAIR)]}/turn",
                # f"Actions:  {self.gamedata.Units[(un, gc.ACTIONSPERTURN)]}/turn",
                f"Notes:    {unitnotes}"
            ]
            self._set_text(self.box_unit, "\n".join(ulines))
        else:
            self._set_text(self.box_unit, "No unit at this hex.")

    # ── Helpers ────────────────────────────────────────────────────────

    def _unit_at(self, h: int, w: int) -> int | None: #get unit index at default altitude or else altitude of (h, w)
        """Return the unit index at hex (h, w) at default altitude, or first altitude where a unit is at, or None if no unit on hex."""
        if self.engine.hexUnits is None:
            return None
        idx = self.engine.hexUnits[(h, w, gc.DEFAULTALTITUDE)]
        if idx != 255: return idx
        for a in range(1, len(self.gamedata.Altitudes)):
            idx = self.engine.hexUnits[(h, w, gc.DEFAULTALTITUDE)]
            if idx != 255: return idx
        if idx == 255: idx = None
        return idx

    def _label(self, parent, text: str, header=False) -> tk.Label: #font size and color based on header or not
        return tk.Label(
            parent, text=text,
            fg="#7878b8" if header else "#d0d0e0",
            bg="#18182a",
            font=("Courier", 8, "bold") if header else ("Courier", 9),
        )

    def _textbox(self, parent, height: int) -> tk.Text: #formatting for text boxes
        t = tk.Text(parent, height=height,
                    bg="#0d0d1a", fg="#e0e0e0",
                    font=("Courier", 8), relief=tk.FLAT,
                    state=tk.DISABLED, wrap=tk.WORD,
                    selectbackground="#3a3a6a")
        return t

    def _set_text(self, widget: tk.Text, text: str):
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.configure(state=tk.DISABLED)

    def _draw_legend(self, parent):
        for p, player in enumerate(self.gamestate.MetadataInitial.PlayersInitial):
            row = tk.Frame(parent, bg="#18182a")
            row.pack(anchor="w")
            tk.Label(row, text="  ", bg=PLAYER_COLORS[p+1], width=2).pack(side=tk.LEFT)
            tk.Label(row, text=f" P{p+1} unit", fg="#c0c0d8", bg="#18182a",
                     font=("Courier", 7)).pack(side=tk.LEFT)

    def _on_scroll(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")

    # ── Public API ─────────────────────────────────────────────────────

    def update_state(self, new_gamestate: GameState): #if new gamestate object needs to be passed for some reason
        self.gamestate = new_gamestate
        self._selected = None
        self._mode     = "idle"
        self._redraw()
        self._update_status()
        self.var_action_hint.set("State updated.")

    def run(self):
        """Start the tkinter event loop (blocking). Call this last."""
        self.root.mainloop()



