"""Generate the public MCP catalog from the Windows FastMCP definitions.

One authoritative signature per tool; no generic tool with arbitrary arguments.
Run from the repository root: python cloud/generate-tools.py
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'desktop/navix/server.py'
OUTPUT = ROOT / 'cloud/src/tool-schemas.mjs'


def schema(annotation):
    if isinstance(annotation, ast.Name):
        result = {'str': {'type': 'string'}, 'int': {'type': 'integer'},
                  'float': {'type': 'number'}, 'bool': {'type': 'boolean'}}.get(annotation.id)
        if result is not None:
            return result
    if isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name):
        if annotation.value.id == 'list':
            return {'type': 'array', 'items': schema(annotation.slice)}
    raise ValueError('Unsupported argument annotation: ' + ast.unparse(annotation))


def main():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    make_app = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'make_app')
    tools = []
    for node in make_app.body:
        if not isinstance(node, ast.FunctionDef) or not any(
                isinstance(dec, ast.Name) and dec.id == 'register' for dec in node.decorator_list):
            continue
        args = node.args.args
        defaults = [None] * (len(args) - len(node.args.defaults)) + node.args.defaults
        props, required = {}, []
        for arg, default in zip(args, defaults):
            props[arg.arg] = schema(arg.annotation)
            if default is None:
                required.append(arg.arg)
            else:
                props[arg.arg]['default'] = ast.literal_eval(default)
        name = node.name
        read_only = name in {'status', 'browser_tabs', 'browser_read', 'browser_snapshot',
                             'browser_screenshot', 'desktop_screenshot', 'desktop_position',
                             'desktop_screen_info', 'files_list', 'files_read',
                             'files_read_binary'}
        destructive = name in {'files_delete', 'files_move', 'files_edit', 'files_write',
                               'files_write_binary', 'command_run', 'command_exec'}
        tools.append({
            'name': name,
            'title': name.replace('_', ' ').capitalize(),
            'description': ast.get_docstring(node) or name,
            'inputSchema': {'type': 'object', 'properties': props, 'required': required,
                            'additionalProperties': False},
            'annotations': {'readOnlyHint': read_only, 'destructiveHint': destructive,
                            'openWorldHint': name.startswith(('browser_', 'command_'))
                            or name == 'files_download'},
            '_meta': {'securitySchemes': [{'type': 'oauth2', 'scopes': ['navix:control']}]},
        })
    if len(tools) != 44:
        raise ValueError(f'Expected 44 tools, got {len(tools)}')
    OUTPUT.write_text('/* Auto-generated from desktop/navix/server.py. Do not edit manually. */\n'
                      'export const PUBLIC_TOOLS = Object.freeze('\
                      + json.dumps(tools, ensure_ascii=False, indent=2) + ');\n', encoding='utf-8')
    print('Generated', len(tools), 'public tool schemas')


if __name__ == '__main__':
    main()
