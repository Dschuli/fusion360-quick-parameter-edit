# Quick Parameters Palette — User Manual

## Purpose

Quick Parameters is intended for rapid testing of parametric Fusion 360 designs. It keeps a small, design-specific set of important user parameters visible while you repeatedly change geometry.

## Opening the palette

The command is available in:

- **Solid → Modify → Quick Parameters**
- **Sketch → Modify → Quick Parameters**

The palette remains open while you work in the model.

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

## Multi-PC use

For shared use across computers, choose a synchronized folder such as Dropbox or OneDrive.

Example:

```text
C:\\Users\\User\\Dropbox\\Fusion360\\QuickParameters
```

The per-design JSON files are synchronized normally. Each PC remembers its own local path to that shared folder, so Dropbox paths may differ between machines.

## Updating the add-in

1. Stop the add-in in **Scripts and Add-Ins**.
2. Replace the add-in folder with the new version.
3. Start it again.

The selected config-folder setting is stored outside the add-in directory and is not lost when updating.
