import adsk.core
import adsk.fusion
import traceback
import json
import os
import re

_app = None
_ui = None
_handlers = []

CMD_ID = 'OpenAI_QuickParametersPalette_Command'
CMD_NAME = 'Quick Parameters'
CMD_DESCRIPTION = 'Open the persistent Quick Parameters palette.'
PALETTE_ID = 'OpenAI_QuickParametersPalette'
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidModifyPanel'
SKETCH_PANEL_ID = 'SketchModifyPanel'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
HTML_FILE = os.path.join(BASE_DIR, 'palette.html')
HTML_URL = 'file:///' + HTML_FILE.replace('\\', '/')

# Persistent app settings live outside the add-in folder so updating the add-in
# doesn't lose the selected config directory.
if os.name == 'nt':
    SETTINGS_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'QuickParametersPalette')
else:
    SETTINGS_DIR = os.path.join(os.path.expanduser('~'), '.quickparameterspalette')

SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')


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


class PaletteHTMLEventHandler(adsk.core.HTMLEventHandler):
    def notify(self, args):
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

        except:
            if _ui:
                _ui.messageBox('Quick Parameters palette error:\n\n' + traceback.format_exc())


class ShowPaletteExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            palette = _ui.palettes.itemById(PALETTE_ID)
            if not palette:
                palette = _ui.palettes.add(
                    PALETTE_ID,
                    'Quick Parameters',
                    HTML_URL,
                    True,
                    True,
                    True,
                    430,
                    560,
                    True
                )

                html_handler = PaletteHTMLEventHandler()
                palette.incomingFromHTML.add(html_handler)
                _handlers.append(html_handler)

                try:
                    palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
                except:
                    pass
            else:
                palette.isVisible = True
                send_model_data()

        except:
            _ui.messageBox('Failed to open Quick Parameters:\n\n' + traceback.format_exc())


class ShowPaletteCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        handler = ShowPaletteExecuteHandler()
        args.command.execute.add(handler)
        _handlers.append(handler)


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

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
