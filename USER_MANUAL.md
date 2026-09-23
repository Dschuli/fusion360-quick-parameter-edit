# Quick Parameters Palette 1.4.0 — User Manual

## Purpose

Quick Parameters is intended for rapid testing of parametric Fusion 360 designs. It keeps a small, design-specific set of important user parameters visible while you repeatedly change geometry.

## Opening the palette

The command is available in:

- **Solid → Modify → Quick Parameters**
- **Sketch → Modify → Quick Parameters**

Starting the add-in, including **Run on Startup**, does not open the palette.
Open it with the command for each new design window. The Quick Parameters
menu/toolbar command toggles it: open when hidden, save position and close when visible.

QPP stays floating and can be dragged and resized. Native docking is disabled
to avoid rearranging other Fusion palettes. Custom collapse/expand is not included.

Close it using the **× button at the top right** or **Esc**. The close button stays
visible with **Quick edit** in a compact top header. Only the content below it
scrolls, so parameter rows cannot slide behind the header buttons.

## Position and size

QPP's open/closed state belongs to each open design window for the current
session. New or reopened designs start with QPP closed. Switching back to a
design restores whether you left QPP open or closed. This state is not saved
between Fusion or add-in sessions; position and size are saved separately.

The **reset arrow beside ×** restores the standard 640-pixel height, keeps your
current width, and requests the rightmost free position. With the Sketch Palette
(SP) visible, it starts 80 pixels above SP, keeping the top controls accessible.
Reset prioritizes the right edge over this starting height; on taller displays,
it may move below another palette to reach the rightmost free position.
Placement stays within the available space; the top cannot move above the viewport.
Without SP, Reset uses its previously observed vertical offset, or a default
starting offset. Reset immediately saves the resulting position and size.
If no suitable space fits or Fusion refuses the height, the status explains it.

QPP saves a separate position and size for each Fusion design when you switch
designs, close the palette, or stop the add-in. When QPP next opens for that design,
it restores the saved placement. Saved designs are identified by their Fusion
file ID, so renaming a design does not lose its placement and identical names
do not share positions. Unsaved designs retain their own placement during the
current session; once saved, their placement can persist between sessions.

A design without a saved placement starts at the Reset position with the
standard 640-pixel height. Reset updates only the current design's placement.
QPP uses the saved preference if its title/close area is
accessible and it does not overlap an API-visible palette. Its bottom may extend
beyond the model viewport. Otherwise it chooses the nearest free
space temporarily. Moving or resizing QPP yourself and then closing it saves
your new preference. QPP does not track other palettes after opening. If no space
fits, it leaves the current position alone.

## Startup appearance

The first opening after loading the add-in starts with a small blank, opaque
window. Once the surrounding palette positions settle, QPP restores the design's
saved position and size (or uses Reset for a new design), and reveals its content. This
avoids briefly displaying the full parameter list in the wrong location.

Startup checks run every 250 milliseconds, wait at least 750 milliseconds and
allow up to three seconds for other palettes to settle. Normal subsequent
openings reuse the initialized window. QPP does not move automatically when
another palette opens later.

## Quick Edit

The upper section contains the parameters selected for the current design.

You can enter:

- values: `4.2 mm`
- parameter references: `cable_width`
- formulas: `cable_width * 0.4`
- functions: `max(3 mm, cable_width / 2)`

Click **Apply** or press **Enter**.

**Reload from design** discards un-applied field edits and reloads the current Fusion expressions.

## Expression autocomplete

Autocomplete appears while typing parameter/function names.

Example:

```text
2 * a_ca
```

Matching parameters are shown automatically.

Controls:

- **Arrow Up / Down** — move through suggestions
- **Enter / Tab** — insert selected suggestion
- **Mouse click** — insert suggestion
- **Esc** — close suggestions

Fusion Favorites are ranked first. Common functions/constants are shown separately.

## Invalid expressions

If Fusion rejects an expression:

- the entire Apply operation is rolled back
- no partial parameter update is kept
- the offending input field is highlighted in red
- the invalid text remains visible for correction
- focus moves to the failed field

Fusion itself performs the final expression validation.

## Manage Parameters

Click **Manage parameters…** to choose which user parameters appear in Quick Edit.

Available tools:

- text filter
- Favorites first
- Name A–Z / Z–A
- Selected first / Unselected first
- Select visible
- Clear visible
- individual checkboxes

Click **Apply selection** to save the choices for the current design.

Parameters that no longer exist in the active design are omitted from Quick edit
and the manager's selection when QPP reloads the design data. This includes
parameters added during a previous session without saving the Fusion design.
Use **Reload from design** to refresh the view after changes in Fusion.
Applying the selection also removes stale parameter names from the JSON config.

## Per-design configuration

Each Fusion design uses its own JSON config file, for example:

```text
Cable Clips.json
ESP Box.json
```

The filename is based on the Fusion design/data-file name rather than its version number.

The JSON file stores only the selected parameter names. Parameter values and expressions remain stored in Fusion.

If no config exists yet for a design, Fusion Favorites are used as the initial proposed selection.

## Config folder

The config folder is shown at the bottom of the palette.

Click **Config folder…** to change it. The folder picker opens at the currently selected location.

The folder choice is remembered separately on each PC.

Position and size are also stored locally, separately from the parameter-selection
files. The settings file is `%APPDATA%\QuickParametersPalette\settings.json` on
Windows or `~/.quickparameterspalette/settings.json` on macOS. Open/closed state
is held only in memory.

## Multi-PC use

For shared use across computers, choose a synchronized folder such as Dropbox or OneDrive.

Example:

```text
C:\\Users\\User\\Dropbox\\Fusion360\\QuickParameters
```

The per-design JSON files are synchronized normally. Each PC remembers its own local path to that shared folder, so Dropbox paths may differ between machines.

Palette positions and sizes are local to each computer and are not synchronized
through the config folder.

## Updating the add-in

1. Stop the add-in in **Scripts and Add-Ins**.
2. Replace the add-in folder with the new version.
3. Start it again.

The selected config-folder setting is stored outside the add-in directory and is not lost when updating.

Per-design placements from 1.4.0 are retained. When upgrading from 1.3, each design
starts at Reset on its first QPP opening because the old shared position is not a
per-design placement. Restarting the add-in clears all open/closed states.

## Placement diagnostics

Diagnostics are written to a file, not displayed in the palette. On Windows,
the file is `%APPDATA%\QuickParametersPalette\palette_diagnostics.json`; on macOS,
it is `~/.quickparameterspalette/palette_diagnostics.json`.
It keeps the latest 20 snapshots, including viewport bounds, palette geometry,
and Fusion version. Include this file when reporting a positioning problem.
