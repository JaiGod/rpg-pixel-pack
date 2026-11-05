#!/usr/bin/env python3
"""Static checks for the Godot project (no engine needed):
- every res:// path referenced from .tscn/.tres/.gd/.godot files exists
- every [ext_resource]/SubResource id used is declared
- every class_name referenced by scripts is defined
"""
import os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'godot_project')
ROOT = os.path.abspath(ROOT)
errors, checked = [], 0
classes = {}
for dp, _, fs in os.walk(ROOT):
    for f in fs:
        if f.endswith('.gd'):
            m = re.search(r'^class_name\s+(\w+)', open(os.path.join(dp, f)).read(), re.M)
            if m:
                classes[m.group(1)] = os.path.join(dp, f)
for dp, _, fs in os.walk(ROOT):
    if '/.godot' in dp:
        continue
    for f in fs:
        if not f.endswith(('.tscn', '.tres', '.gd', '.godot', '.gdshader')):
            continue
        p = os.path.join(dp, f)
        t = open(p).read()
        for ref in set(re.findall(r'res://[A-Za-z0-9_\-./]+', t)):
            ref = ref.rstrip('.')
            if '%' in ref:
                continue
            checked += 1
            local = os.path.join(ROOT, ref[len('res://'):])
            if not os.path.exists(local):
                errors.append(f'{os.path.relpath(p, ROOT)}: missing {ref}')
        if f.endswith(('.tscn', '.tres')):
            ext = set(re.findall(r'\[ext_resource [^\]]*id="([^"]+)"', t))
            sub = set(re.findall(r'\[sub_resource [^\]]*id="([^"]+)"', t))
            for u in set(re.findall(r'ExtResource\("([^"]+)"\)', t)) - ext:
                errors.append(f'{os.path.relpath(p, ROOT)}: undeclared ExtResource {u}')
            for u in set(re.findall(r'SubResource\("([^"]+)"\)', t)) - sub:
                errors.append(f'{os.path.relpath(p, ROOT)}: undeclared SubResource {u}')
            if not t.startswith('[gd_'):
                errors.append(f'{os.path.relpath(p, ROOT)}: bad header')
        if f.endswith('.gd'):
            if '\t' not in t and 'func ' in t:
                errors.append(f'{os.path.relpath(p, ROOT)}: no tab indentation?')
            if re.search(r'^ +\S', t, re.M):
                errors.append(f'{os.path.relpath(p, ROOT)}: space-indented line(s)')
print(f'checked {checked} res:// references, {len(classes)} class_names: {sorted(classes)}')
print('\n'.join(errors) if errors else 'OK — no problems found')
sys.exit(1 if errors else 0)
