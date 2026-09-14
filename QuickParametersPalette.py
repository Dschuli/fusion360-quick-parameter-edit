import adsk.core
import adsk.fusion
import traceback
import json
import os
import re
import time
import hashlib
from datetime import datetime, timezone

_app = None
_ui = None
_handlers = []
_placement_pending = False
_placement_baseline = None
_placement_initialized = False
_startup_check = None
_startup_generation = 0
_startup_full_size = None

CMD_ID = 'OpenAI_QuickParametersPalette_Command'
CMD_NAME = 'Quick Parameters'
CMD_DESCRIPTION = 'Show or hide the Quick Parameters palette.'
PALETTE_ID = 'OpenAI_QuickParametersPalette'
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidModifyPanel'
SKETCH_PANEL_ID = 'SketchModifyPanel'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
HTML_FILE = os.path.join(BASE_DIR, 'palette.html')
# A changed page must not reuse the embedded browser's cached previous layout.
with open(HTML_FILE, 'rb') as _html_source:
    _html_revision = hashlib.sha256(_html_source.read()).hexdigest()[:16]
HTML_URL = 'file:///' + HTML_FILE.replace('\\', '/') + '?revision=' + _html_revision

# Persistent app settings live outside the add-in folder so updating the add-in
# doesn't lose the selected config directory.
if os.name == 'nt':
    SETTINGS_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'QuickParametersPalette')
else:
    SETTINGS_DIR = os.path.join(os.path.expanduser('~'), '.quickparameterspalette')

SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')
PALETTE_DIAGNOSTICS_FILE = os.path.join(SETTINGS_DIR, 'palette_diagnostics.json')


def record_palette_diagnostics(stage):
    """Read the full palette collection without changing any palette's layout."""
    snapshot = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'stage': stage,
        'palettes': [],
    }
    try:
        snapshot['fusionVersion'] = _app.version
        snapshot['activeCommand'] = _ui.activeCommand
        design = get_design()
        edit_object = design.activeEditObject if design else None
        snapshot['activeEditObjectType'] = edit_object.objectType if edit_object else None
    except Exception as exc:
        snapshot['contextError'] = str(exc)

    try:
        palettes = _ui.palettes
        snapshot['paletteCount'] = palettes.count
        for index in range(palettes.count):
            entry = {'index': index}
            try:
                palette = palettes.item(index)
                for name in ('id', 'name', 'isNative', 'isVisible', 'isValid',
                             'left', 'top', 'width', 'height', 'dockingState',
                             'dockingOption', 'isDockedInCanvas'):
                    try:
                        value = getattr(palette, name)
                        if value is not None and not isinstance(value, (str, int, float, bool)):
                            value = str(value)
                        entry[name] = value
                    except Exception as exc:
                        entry.setdefault('propertyErrors', {})[name] = str(exc)
            except Exception as exc:
                entry['error'] = str(exc)
            snapshot['palettes'].append(entry)
    except Exception as exc:
        snapshot['collectionError'] = str(exc)

    try:
        ensure_settings_dir()
        try:
            with open(PALETTE_DIAGNOSTICS_FILE, 'r', encoding='utf-8') as f:
                previous = json.load(f)
            if not isinstance(previous, list):
                previous = []
        except (OSError, ValueError):
            previous = []
        with open(PALETTE_DIAGNOSTICS_FILE, 'w', encoding='utf-8') as f:
            json.dump((previous + [snapshot])[-20:], f, indent=2, ensure_ascii=False)
    except Exception as exc:
        # Diagnostics must never prevent QPP from opening.
        try:
            _app.log('QPP palette diagnostics could not be saved: ' + str(exc))
        except Exception:
            pass


def ensure_settings_dir():
    os.makedirs(SETTINGS_DIR, exist_ok=True)


def load_settings():
    ensure_settings_dir()
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except:
        return {}


def save_settings(data):
    ensure_settings_dir()
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_config_folder():
    settings = load_settings()
    folder = settings.get('configFolder', '')
    if folder and os.path.isdir(folder):
        return folder
    return ''


def set_config_folder(folder):
    settings = load_settings()
    settings['configFolder'] = folder
    save_settings(settings)


def get_design():
    if not _app:
        return None
    return adsk.fusion.Design.cast(_app.activeProduct)


def get_design_name():
    """
    Prefer DataFile.name because Fusion stores the version separately from
    the data-file name. Fall back to Document.name for unsaved/local docs.
    """
    doc = _app.activeDocument if _app else None
    if not doc:
        return 'Untitled'

    try:
        if doc.dataFile:
            name = doc.dataFile.name
            if name:
                return name
    except:
        pass

    try:
        name = doc.name or 'Untitled'
    except:
        name = 'Untitled'

    # Defensive fallback only: remove a trailing " v123" if Fusion/document
    # text happens to include one.
    name = re.sub(r'\s+[vV]\d+\s*$', '', name)
    return name or 'Untitled'


def safe_filename(name):
    # Windows-invalid filename characters + trailing spaces/dots.
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip().rstrip('. ')
    return name or 'Untitled'


def config_path_for_design():
    folder = get_config_folder()
    if not folder:
        return ''
    return os.path.join(folder, safe_filename(get_design_name()) + '.json')


def load_parameter_names():
    path = config_path_for_design()
    if not path or not os.path.isfile(path):
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [str(x).strip() for x in data.get('parameters', []) if str(x).strip()]
    except:
        return []


def save_parameter_names(names):
    path = config_path_for_design()
    if not path:
        raise RuntimeError('No config folder selected.')

    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)

    clean = []
    seen = set()
    for name in names:
        n = str(name).strip()
        if n and n not in seen:
            clean.append(n)
            seen.add(n)

    payload = {
        'design': get_design_name(),
        'parameters': clean
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

    return clean


def current_config_info():
    folder = get_config_folder()
    path = config_path_for_design()
    return {
        'folder': folder,
        'file': path,
        'fileName': os.path.basename(path) if path else '',
        'designName': get_design_name(),
        'exists': bool(path and os.path.isfile(path))
    }


def model_data():
    design = get_design()
    selected = load_parameter_names()
    cfg = current_config_info()

    result = {
        'parameters': [],
        'allParameters': [],
        'selectedNames': selected,
        'status': '',
        'config': cfg
    }

    if not design:
        result['status'] = 'No active Fusion design.'
        return result

    # If there is no design config yet, start with Fusion Favorites as a
    # sensible initial proposed selection. It won't be saved until the user
    # applies a selection.
    if not cfg['exists']:
        favorites = []
        ups = design.userParameters
        for i in range(ups.count):
            p = ups.item(i)
            try:
                if p.isFavorite:
                    favorites.append(p.name)
            except:
                pass
        selected = favorites
        result['selectedNames'] = selected

    missing = []

    # Quick-edit subset.
    for name in selected:
        p = design.userParameters.itemByName(name)
        if p:
            result['parameters'].append({
                'name': name,
                'expression': p.expression,
                'value': p.value,
                'unit': p.unit
            })
        else:
            result['parameters'].append({
                'name': name,
                'expression': '',
                'missing': True
            })
            missing.append(name)

    # Full user parameter list for manager.
    ups = design.userParameters
    for i in range(ups.count):
        p = ups.item(i)
        favorite = False
        try:
            favorite = bool(p.isFavorite)
        except:
            pass

        result['allParameters'].append({
            'name': p.name,
            'expression': p.expression,
            'unit': p.unit,
            'selected': p.name in selected,
            'favorite': favorite
        })

    if not get_config_folder():
        result['status'] = 'Choose a config folder to save this design’s Quick Parameters.'
    elif not cfg['exists']:
        result['status'] = 'No config yet — Favorites shown as initial selection.'
    elif missing:
        result['status'] = 'Missing: ' + ', '.join(missing)
    else:
        result['status'] = 'Ready'

    return result


def send_model_data():
    palette = _ui.palettes.itemById(PALETTE_ID)
    if palette:
        palette.sendInfoToHTML('modelData', json.dumps(model_data()))



class ParameterExpressionError(Exception):
    def __init__(self, parameter_name, message):
        super().__init__(message)
        self.parameter_name = parameter_name
        self.message = message

def apply_expressions(data):
    design = get_design()
    if not design:
        return {'ok': False, 'message': 'No active Fusion design.'}

    values = data.get('values', {})
    selected = load_parameter_names()

    # If there isn't a saved design file yet, use the currently displayed
    # field names sent by HTML as the selected set.
    if not selected:
        selected = list(values.keys())

    old = {}
    changed = []

    try:
        for name in selected:
            p = design.userParameters.itemByName(name)
            if p:
                old[name] = p.expression

        for name in selected:
            p = design.userParameters.itemByName(name)
            if not p or name not in values:
                continue

            expr = str(values[name]).strip()
            if not expr:
                raise ValueError(f'{name}: expression is empty')

            if expr != p.expression:
                try:
                    p.expression = expr
                except Exception as inner_exc:
                    raise ParameterExpressionError(name, str(inner_exc))
                changed.append(name)

        design.computeAll()

        return {
            'ok': True,
            'message': ('Applied: ' + ', '.join(changed)) if changed else 'No changes.'
        }

    except Exception as exc:
        for name, expr in old.items():
            try:
                p = design.userParameters.itemByName(name)
                if p:
                    p.expression = expr
            except:
                pass
        try:
            design.computeAll()
        except:
            pass

        if isinstance(exc, ParameterExpressionError):
            return {
                'ok': False,
                'message': f'{exc.parameter_name}: {exc.message}',
                'errorParameter': exc.parameter_name
            }

        # A later compute failure can be geometric rather than an invalid
        # expression, so no single field is blamed unless Fusion rejected
        # that parameter expression directly.
        return {'ok': False, 'message': str(exc), 'errorParameter': ''}


def update_selection(data):
    try:
        design = get_design()
        if not design:
            return {'ok': False, 'message': 'No active Fusion design.'}

        if not get_config_folder():
            return {'ok': False, 'message': 'Choose a config folder first.'}

        requested = data.get('names', [])
        valid = set()
        ups = design.userParameters
        for i in range(ups.count):
            valid.add(ups.item(i).name)

        names = [n for n in requested if n in valid]
        save_parameter_names(names)

        return {
            'ok': True,
            'message': f'Selection saved for {get_design_name()} ({len(names)} parameters).'
        }
    except Exception as exc:
        return {'ok': False, 'message': str(exc)}


def choose_config_folder():
    try:
        dialog = _ui.createFolderDialog()
        dialog.title = 'Choose Quick Parameters config folder'

        current_folder = get_config_folder()
        if current_folder and os.path.isdir(current_folder):
            try:
                dialog.initialDirectory = current_folder
            except:
                pass

        result = dialog.showDialog()

        if result != adsk.core.DialogResults.DialogOK:
            return {'ok': False, 'cancelled': True, 'message': 'Folder selection cancelled.'}

        folder = dialog.folder
        if not folder:
            return {'ok': False, 'message': 'No folder selected.'}

        os.makedirs(folder, exist_ok=True)
        set_config_folder(folder)

        return {
            'ok': True,
            'message': 'Config folder selected.',
            'folder': folder
        }
    except Exception as exc:
        return {'ok': False, 'message': str(exc)}


def palette_geometry(palette):
    return {key: int(getattr(palette, key)) for key in ('left', 'top', 'width', 'height')}


def valid_geometry(value):
    return (isinstance(value, dict) and
            all(type(value.get(k)) is int for k in ('left', 'top', 'width', 'height')) and
            value['width'] > 0 and value['height'] > 0)


def geometry_changed(current, baseline):
    return any(abs(current[k] - baseline[k]) > 2 for k in current)


def remember_palette_position(palette):
    """A temporary placement is not a new preference unless the user moves it."""
    global _placement_pending, _placement_baseline, _startup_check
    try:
        if not _placement_pending and _placement_baseline is not None:
            current = palette_geometry(palette)
            if geometry_changed(current, _placement_baseline):
                settings = load_settings()
                settings['preferredPaletteGeometry'] = current
                save_settings(settings)
    except Exception as exc:
        _app.log('QPP position could not be saved: ' + str(exc))
    finally:
        _placement_pending = False
        _placement_baseline = None
        _startup_check = None


def nearest_palette_position(preferred, bounds, obstacles, gap=8, rightmost=False):
    """Keep the preferred rectangle if free; otherwise choose the nearest fit."""
    x, y = preferred['left'], preferred['top']
    w, h = preferred['width'], preferred['height']
    left, top, right, bottom = bounds

    def fits(px, py):
        return (left <= px and top <= py and px + w <= right and py + h <= bottom and
                all(px + w + gap <= a or px >= c + gap or
                    py + h + gap <= b or py >= d + gap for a, b, c, d in obstacles))

    # A user may deliberately place the lower part outside the canvas. Keep
    # that choice when the title/close area remains reachable and no palette
    # actually overlaps it. Padding applies only to newly proposed positions.
    accessible = left <= x and x + w <= right and top <= y and y + 64 <= bottom
    clear = all(x + w <= a or x >= c or y + h <= b or y >= d
                for a, b, c, d in obstacles)
    if accessible and clear and not rightmost:
        return x, y
    xs = {x, left, right - w}
    ys = {y, top, bottom - h}
    for a, b, c, d in obstacles:
        xs.update((a - gap - w, c + gap))
        ys.update((b - gap - h, d + gap))
    candidates = [(px, py) for px in xs for py in ys if fits(px, py)]
    if rightmost:
        return min(candidates, key=lambda p: (abs(p[1] - y), -p[0], p[1]), default=None)
    return min(candidates, key=lambda p: ((p[0]-x)**2 + (p[1]-y)**2, -p[0], p[1]),
               default=None)


def restore_startup_size(palette):
    """Never leave the temporary startup frame as the usable palette."""
    global _startup_full_size
    if _startup_full_size is None:
        return
    width, height = _startup_full_size
    if (palette.width, palette.height) != (width, height):
        palette.setSize(width, height)
    if (palette.width, palette.height) != (width, height):
        raise RuntimeError('Fusion did not restore the startup frame size')
    _startup_full_size = None


def finish_open_placement(palette, allow_hidden=False, reset=False):
    """Run once, after the visible HTML browser has reported that it loaded."""
    global _placement_pending, _placement_baseline, _placement_initialized
    if not _placement_pending or (not palette.isVisible and not allow_hidden):
        return
    _placement_pending = False
    try:
        settings = load_settings()
        preferred = settings.get('preferredPaletteGeometry')
        if (valid_geometry(preferred) and preferred['width'] <= 160 and
                preferred['height'] <= 260):
            # Recover a collapsed strip accidentally saved during versions
            # 1.2.13–1.2.20. Preserve its location, but restore full size.
            preferred = dict(preferred, width=430, height=640)
            settings.pop('collapseRestoreGeometry', None)
            settings['preferredPaletteGeometry'] = preferred
            save_settings(settings)
        if not valid_geometry(preferred):
            preferred = palette_geometry(palette)
            if _startup_full_size is not None:
                preferred.update(width=_startup_full_size[0], height=_startup_full_size[1])
            settings['preferredPaletteGeometry'] = preferred
            save_settings(settings)
        viewport = _app.activeViewport
        origin = viewport.viewToScreen(adsk.core.Point2D.create(0, 0))
        corner = viewport.viewToScreen(adsk.core.Point2D.create(viewport.width, viewport.height))
        bounds = (int(origin.x), int(origin.y), int(corner.x), int(corner.y))
        if reset:
            offset = settings.get('standardPaletteTopOffset', 140)
            if type(offset) is not int or offset < 0:
                offset = 140
            preferred = dict(left=bounds[2] - palette.width, top=max(bounds[1], bounds[1] + offset - 80),
                             width=int(palette.width), height=640)
        obstacles = []
        for index in range(_ui.palettes.count):
            other = _ui.palettes.item(index)
            if other.id == PALETTE_ID or not other.isVisible:
                continue
            rect = (other.left, other.top, other.left + other.width, other.top + other.height)
            if (other.width > 0 and other.height > 0 and rect[0] < bounds[2] and
                    rect[2] > bounds[0] and rect[1] < bounds[3] and rect[3] > bounds[1]):
                obstacles.append(rect)
                if reset and 'ToolPropertyPanelSketch Palette' in other.id:
                    preferred['top'] = max(bounds[1], int(other.top) - 80)
                    settings['standardPaletteTopOffset'] = max(0, int(other.top) - bounds[1])
        position = nearest_palette_position(preferred, bounds, obstacles, rightmost=reset)
        if position is None:
            _app.log('QPP placement: no free space fits; leaving the current layout.')
            if reset:
                return {'ok': False, 'message': 'No free space fits the standard height; position unchanged.'}
        else:
            current = palette_geometry(palette)
            if (current['left'], current['top']) != position:
                if not palette.setPosition(*position):
                    if (palette.left, palette.top) != position:
                        raise RuntimeError('Fusion rejected setPosition')
            if (palette.width, palette.height) != (preferred['width'], preferred['height']):
                if not palette.setSize(preferred['width'], preferred['height']) and not reset:
                    raise RuntimeError('Fusion rejected setSize')
            if reset or _startup_full_size is not None:
                # Resizing a floating palette can shift its origin in Fusion.
                if (palette.left, palette.top) != position:
                    if not palette.setPosition(*position) and (palette.left, palette.top) != position:
                        raise RuntimeError('Fusion rejected the reset position')
            if reset:
                # Reset is an explicit user choice, unlike automatic collision
                # avoidance. Persist the actual accepted geometry immediately.
                settings['preferredPaletteGeometry'] = palette_geometry(palette)
                save_settings(settings)
        record_palette_diagnostics('after placement')
        message = 'Position reset.'
        if reset and palette.height != 640:
            message = 'Position reset and saved. Fusion retained height ' + str(palette.height) + ' px.'
        return {'ok': True, 'message': message}
    except Exception as exc:
        _app.log('QPP placement skipped: ' + str(exc))
        return {'ok': False, 'message': 'Position reset failed: ' + str(exc)}
    finally:
        try:
            restore_startup_size(palette)
        except Exception as exc:
            _app.log('QPP startup resize failed: ' + str(exc))
        # Record what Fusion actually accepted, rather than the requested rectangle.
        _placement_baseline = palette_geometry(palette)
        _placement_initialized = True

        try:
            palette.sendInfoToHTML('placementComplete', '{}')
        except Exception as exc:
            _app.log('QPP content reveal notification failed: ' + str(exc))


def begin_startup_placement(palette):
    """Bound the initial geometry sampling to three seconds, never track later."""
    global _startup_check, _startup_generation
    if not _placement_pending or _startup_check is not None:
        return
    if _placement_initialized:
        finish_open_placement(palette)
        return
    _startup_generation += 1
    now = time.monotonic()
    _startup_check = dict(token=_startup_generation, started=now, changed=now,
                          signature=None, samples=0, initial=palette_geometry(palette))
    sample_startup_placement(palette, _startup_generation)


def sample_startup_placement(palette, token):
    global _startup_check, _placement_pending, _placement_baseline, _placement_initialized
    check = _startup_check
    if (check is None or token != check['token'] or
            not _placement_pending or not palette.isVisible):
        return
    now = time.monotonic()
    check['samples'] += 1
    try:
        current = palette_geometry(palette)
        if any(abs(current[k] - check['initial'][k]) > 2 for k in ('left', 'top')):
            # Avoid overriding a drag while the initial check is in progress.
            _placement_pending = False
            _placement_initialized = True
            _placement_baseline = check['initial']
            _startup_check = None
            restore_startup_size(palette)
            record_palette_diagnostics('startup check cancelled: QPP moved')
            palette.sendInfoToHTML('placementComplete', '{}')
            return
        rows = []
        sketch_visible = False
        for index in range(_ui.palettes.count):
            other = _ui.palettes.item(index)
            if other.id != PALETTE_ID and other.isVisible:
                rows.append((other.id, other.left, other.top, other.width, other.height))
                if ('ToolPropertyPanelSketch Palette' in other.id and
                        other.width > 0 and other.height > 0):
                    sketch_visible = True
        signature = tuple(sorted(rows))
        if signature != check['signature']:
            check['signature'] = signature
            check['changed'] = now
            record_palette_diagnostics('startup geometry sample ' + str(check['samples']))
        design = get_design()
        edit_object = design.activeEditObject if design else None
        expects_sketch = bool(edit_object and edit_object.objectType == 'adsk::fusion::Sketch')
        stable = (now - check['started'] >= 0.75 and now - check['changed'] >= 0.5 and
                  (not expects_sketch or sketch_visible))
    except Exception as exc:
        stable = False
        _app.log('QPP startup geometry sample failed: ' + str(exc))
    expired = now - check['started'] >= 3 or check['samples'] >= 13
    if stable or expired:
        _startup_check = None
        record_palette_diagnostics('startup geometry stable' if stable else 'startup geometry timeout')
        finish_open_placement(palette)
    else:
        palette.sendInfoToHTML('sampleStartupPlacement', json.dumps({'token': token}))


class PaletteClosedHandler(adsk.core.UserInterfaceGeneralEventHandler):
    def notify(self, args):
        palette = _ui.palettes.itemById(PALETTE_ID)
        if palette:
            remember_palette_position(palette)


class PaletteHTMLEventHandler(adsk.core.HTMLEventHandler):
    def notify(self, args):
        global _startup_check, _placement_pending
        try:
            html_args = adsk.core.HTMLEventArgs.cast(args)
            action = html_args.action

            try:
                data = json.loads(html_args.data) if html_args.data else {}
            except:
                data = {}

            palette = _ui.palettes.itemById(PALETTE_ID)
            if not palette:
                return

            if action in ('ready', 'reload'):
                send_model_data()
                if action == 'ready':
                    begin_startup_placement(palette)

            elif action == 'placementReady':
                begin_startup_placement(palette)

            elif action == 'startupPlacementSample':
                sample_startup_placement(palette, data.get('token'))

            elif action == 'resetPosition':
                _startup_check = None
                _placement_pending = True
                result = finish_open_placement(palette, reset=True)
                palette.sendInfoToHTML('resetPositionResult', json.dumps(result))

            elif action == 'apply':
                result = apply_expressions(data)
                palette.sendInfoToHTML('applyResult', json.dumps(result))
                if result.get('ok'):
                    send_model_data()

            elif action == 'saveSelection':
                result = update_selection(data)
                palette.sendInfoToHTML('selectionResult', json.dumps(result))
                if result.get('ok'):
                    send_model_data()

            elif action == 'chooseConfigFolder':
                result = choose_config_folder()
                palette.sendInfoToHTML('folderResult', json.dumps(result))
                if result.get('ok'):
                    send_model_data()

            elif action == 'closePalette':
                remember_palette_position(palette)
                palette.isVisible = False

        except:
            if _ui:
                _ui.messageBox('Quick Parameters palette error:\n\n' + traceback.format_exc())


class ShowPaletteExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        global _placement_pending, _placement_baseline, _placement_initialized
        global _startup_full_size
        try:
            record_palette_diagnostics('before QPP opens')
            palette = _ui.palettes.itemById(PALETTE_ID)
            if palette and palette.isVisible:
                remember_palette_position(palette)
                palette.isVisible = False
                record_palette_diagnostics('QPP toggled closed')
                return
            opening = not palette or not palette.isVisible
            if opening:
                _placement_pending = True
                _placement_baseline = None
            if not palette:
                _placement_initialized = False
                preferred = load_settings().get('preferredPaletteGeometry')
                _startup_full_size = (430, 640)
                if valid_geometry(preferred) and not (preferred['width'] <= 160 and preferred['height'] <= 260):
                    _startup_full_size = (preferred['width'], preferred['height'])
                palette = _ui.palettes.add(
                    PALETTE_ID,
                    'Quick Parameters',
                    HTML_URL,
                    True,
                    False,  # Top HTML close control replaces the native footer.
                    True,
                    200,
                    100,
                    True
                )

                html_handler = PaletteHTMLEventHandler()
                palette.incomingFromHTML.add(html_handler)
                _handlers.append(html_handler)
                closed_handler = PaletteClosedHandler()
                palette.closed.add(closed_handler)
                _handlers.append(closed_handler)

                try:
                    # Keep dragging from docking QPP into Fusion's native layout.
                    palette.dockingOption = adsk.core.PaletteDockingOptions.PaletteDockOptionsNone
                    # Right docking rearranges SP before collision detection;
                    # floating again then restores SP into the chosen space.
                    # Start floating so startup sampling sees the real layout.
                    palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateFloating
                except Exception as exc:
                    _app.log('QPP could not configure floating-only mode: ' + str(exc))
            else:
                if opening and _placement_initialized:
                    # This browser has already rendered successfully. Move the
                    # existing hidden palette before revealing it; never do
                    # this to a newly created, uninitialized browser.
                    finish_open_placement(palette, allow_hidden=True)
                palette.isVisible = True
                if opening and not _placement_pending:
                    _placement_baseline = palette_geometry(palette)
                send_model_data()
                if opening and _placement_pending:
                    palette.sendInfoToHTML('preparePlacement', '{}')

            record_palette_diagnostics('after QPP opens')

        except:
            _ui.messageBox('Failed to open Quick Parameters:\n\n' + traceback.format_exc())


class ShowPaletteCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        handler = ShowPaletteExecuteHandler()
        args.command.execute.add(handler)
        _handlers.append(handler)


def discard_previous_palette():
    """Do not reuse a page or event handlers left by an earlier add-in load."""
    global _placement_pending, _placement_baseline, _placement_initialized
    global _startup_check, _startup_generation
    global _startup_full_size
    _startup_full_size = None
    _startup_generation += 1
    _startup_check = None
    _placement_pending = False
    _placement_baseline = None
    _placement_initialized = False
    palette = _ui.palettes.itemById(PALETTE_ID)
    if palette:
        # The old frame may be a collapsed experiment. Do not save its size.
        palette.deleteMe()


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        discard_previous_palette()

        cmd_def = _ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = _ui.commandDefinitions.addButtonDefinition(
                CMD_ID,
                CMD_NAME,
                CMD_DESCRIPTION,
                './resources/QuickParameters'
            )

        created_handler = ShowPaletteCreatedHandler()
        cmd_def.commandCreated.add(created_handler)
        _handlers.append(created_handler)

        # Add to Solid -> Modify.
        workspace = _ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID) if workspace else None
        if panel and not panel.controls.itemById(CMD_ID):
            control = panel.controls.addCommand(cmd_def)
            control.isPromoted = True

        # Add the same command to Sketch -> Modify.
        # Use allToolbarPanels because the Sketch panel is contextual and may
        # not be visible when the add-in starts.
        sketch_panel = _ui.allToolbarPanels.itemById(SKETCH_PANEL_ID)
        if sketch_panel and not sketch_panel.controls.itemById(CMD_ID):
            sketch_control = sketch_panel.controls.addCommand(cmd_def)
            sketch_control.isPromoted = True

    except:
        if _ui:
            _ui.messageBox('Quick Parameters failed to start:\n\n' + traceback.format_exc())


def stop(context):
    try:
        if _ui:
            palette = _ui.palettes.itemById(PALETTE_ID)
            if palette:
                if palette.isVisible:
                    remember_palette_position(palette)
                palette.deleteMe()

            workspace = _ui.workspaces.itemById(WORKSPACE_ID)
            panel = workspace.toolbarPanels.itemById(PANEL_ID) if workspace else None
            if panel:
                control = panel.controls.itemById(CMD_ID)
                if control:
                    control.deleteMe()

            sketch_panel = _ui.allToolbarPanels.itemById(SKETCH_PANEL_ID)
            if sketch_panel:
                sketch_control = sketch_panel.controls.itemById(CMD_ID)
                if sketch_control:
                    sketch_control.deleteMe()

            cmd_def = _ui.commandDefinitions.itemById(CMD_ID)
            if cmd_def:
                cmd_def.deleteMe()

        _handlers.clear()
    except:
        pass
