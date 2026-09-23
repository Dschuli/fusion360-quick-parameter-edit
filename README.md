# Quick Parameters Palette for Fusion 360

A lightweight Fusion 360 add-in for quickly editing a selected subset of user parameters while testing parametric designs.

Instead of repeatedly opening **Change Parameters** and searching through a large parameter list, Quick Parameters provides a persistent palette containing only the parameters you want to work with.

## Features

- Persistent quick-edit palette
- Floating palette with position and size remembered per design across sessions
- Avoids overlap with visible palettes when opening, without moving afterward
- Fixed header with position reset and Close controls
- Menu command toggles the palette open and closed
- Edit values, formulas, and parameter references
- Parameter autocomplete while typing
- Invalid expressions are highlighted and rolled back safely
- Filterable/sortable parameter manager
- Fusion Favorites shown first
- Per-design parameter selections
- Per-design open/closed state for the current session; newly opened designs start closed
- Missing parameters omitted from Quick edit and the parameter-manager selection
- Config files can be stored in Dropbox/OneDrive for multi-PC use
- Available in **Solid → Modify** and **Sketch → Modify**

Parameter values stay in the Fusion design. The JSON config stores only which parameters are shown in Quick Parameters.

![Quick Parameters Palette in Fusion 360](<images/Screenshot QPP.png>)

*Quick Parameters Palette with quick editing and parameter selection controls in Fusion 360.*

## Installation

1. Download or clone the repository.
2. Keep the `QuickParametersPalette` folder in a permanent location.
3. In Fusion 360 open **Utilities → Scripts and Add-Ins → Add-Ins**.
4. Click **+** and select the `QuickParametersPalette` folder.
5. Run the add-in.
6. Optionally enable **Run on Startup**.

## Version 1.4.0

QPP remembers position and size separately for each design across sessions.
Open/closed state is separate for each open design window and lasts only for the
current session. New and reopened designs start with QPP closed, even when the
add-in runs on startup. Switching back restores whether you left QPP open or closed.

Reset uses the rightmost free position, including on scaled displays, and avoids
other visible palettes. Native docking is disabled; QPP stays freely movable and
resizable. Designs without saved placement use Reset when you first open QPP.

Missing parameters no longer appear as error rows or invisible selected items in
Manage parameters. Applying a selection removes their stale names from the config.
Nonnumeric parameters no longer cause a numeric-value read error when loading QPP.

On the first opening after loading the add-in, a small blank window briefly
appears while surrounding palettes settle. QPP then restores the current design's
position and size, or uses Reset if that design has no saved placement.

To update, stop the add-in, replace its files and run it again. Your parameter
selections and config-folder setting are retained. Existing 1.4.0 per-design
placements are retained; the single shared position from 1.3 is not assigned to
every design. Each design initially uses Reset until it has its own placement.

## First use

1. Open **Quick Parameters**.
2. Select a **Config folder**.
3. Open **Manage parameters…**.
4. Choose the parameters you want.
5. Click **Apply selection**.

Each design gets its own config file, e.g. `Cable Clips.json`.

## Usage

Enter any valid Fusion expression, for example:

```text
4.2 mm
cable_width * 0.4
max(3 mm, cable_width / 2)
```

Press **Apply** or **Enter** to update the design.

See [USER_MANUAL.md](USER_MANUAL.md) for details.

## Requirements

- Autodesk Fusion 360
- Tested on Windows
- Fusion 360 Python API
- No external Python dependencies

## License

This project is available under the MIT License.

## Contributing

Bug reports, improvements, and pull requests are welcome.

When reporting an issue, include:

* Fusion version
* Operating system
* Steps to reproduce and relevant parameter expressions
* The displayed error and a screenshot where useful

## Acknowledgments

- AI-assisted tools were used to support the coding, documentation, and review process. All resulting changes were reviewed and tested by the project maintainer.
