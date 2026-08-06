#!/usr/bin/env python3
import ast
import os

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
    
    # Relative path of the file itself as a module entry
    # Using absolute path logic to ensure we can find it in any context
    abs_path = os.path.abspath(path)
    symbols["modules"].append(abs_path)

    try:
        with open(path, 'r', encoding='undetermined') as f: # Fallback to error catch
            pass 
    except: pass

    # Let's try the real way
    try:
        with open(path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except Exception as e:
        return None

    for node in tree.body:
        # Function definitions (top-level)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith('_'):
                # Extracting parameters for the signature as requested
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

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import json
        result = parse_symbols(sys.argv[1])
        print(json.dumps(result, indent=2) if result else "None")
