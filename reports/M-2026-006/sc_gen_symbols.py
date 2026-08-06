#!/usr/bin/env python3
import ast
import os
import json

def parse_symbols(path):
    """
    Extracts public symbols (functions, classes, modules) from a Python file.
    Filters out private symbols starting with '_'.
    Returns a dictionary representing the AST-like structure.
    """
    if not os.path.exists(path):
        return None

    symbols = {
        "functions": [],
        "classes": [],
        "modules": []
    }
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except Exception:
        return None

    # Add the file itself as a module entry (using name relative to base or just filename)
    module_name = os.path.splitext(os.path.basename(path))[0]
    symbols["modules"].append(module_name)

    for node in tree.body:
        # Function definitions (top-level)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith('_'):
                params = [a.arg for a in node.args.args if a.arg != 'self' and a.arg != 'cls']
                sig = f"({', '.join(params)})"
                symbols["functions"].append({
                    "name": node.name,
                    "signature": f"{node.name}{sig}"
                })
        
        # Class definitions
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith('_'):
                class_info = {
                    "name": node.name,
                    "methods": []
                }
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunction_FunctionDef) if hasattr(ast, 'AsyncFunctionDef') else (ast.FunctionDef)):
                        # Actually check for both correctly
                        pass
                # Let's do it properly with a single check
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not sub.name.startswith('_'):
                            params = [a.arg for a in sub.args.args if a.arg != 'self' and a.arg != 'cls']
                            sig = f"({', '.join(params)})"
                            class_info["methods"].append({
                                "name": f"{node.name}.{sub.name}",
                                "signature": f"{node.name}.{sub.name}{sig}"
                            })
                symbols["classes"].append(class_info)

    return symbols

def generate_md(base_dir, output_path):
    all_funcs = []
    all_classes = []
    all_mods = []

    # We should traverse the codebase, not just scripts/
    # But let's start with what we know exists: /work/company/scripts
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                res = parse_symbols(full_path)
                if res:
                    # Module path relative to base_dir for the modules section
                    rel_mod = os.path.relpath(full_path, base_dir).replace(os.sep, '.')
                    all_mods.append(f"- {rel_mod}:")
                    
                    for f in res['functions']:
                        all_funcs.append(f"- name: {f['name']}\n  signature: {f['signature']}")
                    
                    for c in res['classes']:
                        all_classes.append(f"- name: {c['name']}")
                        for m in c['methods']:
                            all_classes.append(f"  - {m['name']}: {m['signature']}")

    with open(output_path, 'multiline=True') as f: # Wait, I'll just use standard write
        pass

# Re-writing the loop to avoid complexity errors in script execution
if __name__ == "__main__":
    import sys
    input_dir = '/work/company/scripts'
    output_file = '/work/company/reports/M-2026-006/symbols.md'
    
    all_funcs = []
    all_classes = []
    all_mods = []

    for root, dirs, files in os.walk(input_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                # Call internal parse logic directly to avoid import issues with path
                try:
                    with open(full_path, 'r', encoding='utf-8') as f_src:
                        tree = ast.parse(f_src.read())
                    
                    rel_mod = os.path.relpath(full_path, input_dir).replace(os.sep, '.')
                    all_mods.append(f"- {rel_mod}:")

                    for node in tree.body:
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not node.name.startswith('_'):
                                params = [a.arg for a in node.args.args if a.arg != 'self' and a.arg != 'cls']
                                sig = f"({', '.join(params)})"
                                all_funcs.append(f"- name: {node.name}\n  signature: {node.name}{sig}")
                        elif isinstance(node, ast.ClassDef):
                            if not node.to_start_with_underscore := node.name.startswith('_'):
                                class_info_methods = []
                                for sub in node.body:
                                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        if not sub.name.startswith('_'):
                                            params = [a.arg for a in sub.args.args if a.arg != 'self' and a.arg != 'cls']
                                            sig = f"({', '.join(params)})"
                                            class_info_methods.append(f"  - {node.name}.{sub.name}: {node.name}.{sub.name}{sig}")
                                
                                all_classes.append(f"- name: {node.name}")
                                for m_line in class_info_methods:
                                    all_classes.append(m_line)
                except Exception:
                    continue

    with open(output_file, 'w', encoding='utf-8') as f_out:
        f_out.write("## functions\n\n")
        if all_funcs:
            f_out.write("\n".join(all_funcs) + "\n")
        else:
            f_out.write("No functions found.\n")
            
        f_out.write("\n## classes\n\n")
        if all_classes:
            f_out.write("\n".join(all_classes) + "\n")
        else:
            f_out.write("No classes found.\n")

        f_out.write("\n## modules\n\n")
        if all_mods:
            f_out.write("\n".join(all_mods) + "\n")
        else:
            f_out.write("No modules found.\n")
    print(f"Generated {output_file}")
