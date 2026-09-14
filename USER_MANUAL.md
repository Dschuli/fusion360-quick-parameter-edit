# Quick Parameters Palette 1.3 — User Manual

## Purpose

Quick Parameters is intended for rapid testing of parametric Fusion 360 designs. It keeps a small, design-specific set of important user parameters visible while you repeatedly change geometry.

## Opening the palette

The command is available in:

- **Solid → Modify → Quick Parameters**
- **Sketch → Modify → Quick Parameters**

The palette remains open while you work in the model. The Quick Parameters
menu/toolbar command toggles it: open when hidden, save position and close when visible.

QPP stays floating and can be dragged and resized. Native docking is disabled
to avoid rearranging other Fusion palettes. Custom collapse/expand is not included.

Close it using the **× button at the top right** or **Esc**. The close button stays
visible with **Quick edit** in a compact top header. Only the content below it
scrolls, so parameter rows cannot slide behind the header buttons.

## Position and size

The **reset arrow beside ×** restores the standard 640-pixel height, keeps your
current width, and requests the rightmost free position. With the Sketch Palette
(SP) visible, it starts 80 pixels above SP, keeping the top controls accessible.
Placement stays within the available space; the top cannot move above the viewport.
Without SP, Reset uses its previously observed vertical offset, or a default
starting offset. Reset immediately saves the resulting position and size.
If no suitable space fits or Fusion refuses the height, the status explains it.

QPP remembers position and size when you close it or stop
the add-in. On reopening, it uses that preference if its title/close area is
accessible and it does not overlap an API-visible palette. Its bottom may extend
beyond the model viewport. Otherwise it chooses the nearest free
space temporarily. Moving or resizing QPP yourself and then closing it saves
your new preference. QPP does not track other palettes after opening. If no space
fits, it leaves the current position alone.

## Startup appearance

The first opening after loading the add-in starts with a small blank, opaque
window. Once the surrounding palette positions settle, QPP moves, expands to
your saved size (430 × 640 pixels by default), and reveals its content. This
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
