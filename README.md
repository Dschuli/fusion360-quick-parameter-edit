# Quick Parameters Palette for Fusion 360

A lightweight Fusion 360 add-in for quickly editing a selected subset of user parameters while testing parametric designs.

Instead of repeatedly opening **Change Parameters** and searching through a large parameter list, Quick Parameters provides a persistent palette containing only the parameters you want to work with.

## Features

- Persistent quick-edit palette
- Floating palette with remembered position and size
- Avoids overlap with visible palettes when opening, without moving afterward
- Fixed header with position reset and Close controls
- Menu command toggles the palette open and closed
- Edit values, formulas, and parameter references
- Parameter autocomplete while typing
- Invalid expressions are highlighted and rolled back safely
- Filterable/sortable parameter manager
- Fusion Favorites shown first
- Per-design parameter selections
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

## Version 1.3

QPP remembers your preferred position and size and checks for overlapping visible
palettes when opening. Reset places it in the rightmost available space, above
the Sketch Palette so its header controls remain accessible. Native docking is
disabled; QPP stays freely movable and resizable.

On the first opening after loading the add-in, a small blank window briefly
appears while surrounding palettes settle. QPP then moves, expands to its normal
size and displays its content. Later openings reuse the initialized window.

To update, stop the add-in, replace its files and run it again. Your configuration
folder and saved placement are retained.

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
