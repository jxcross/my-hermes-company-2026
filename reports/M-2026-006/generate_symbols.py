import os
import ast

def run():
    input_dir = '/work/company/scripts'
    output_file = '/work/company/reports/M-2026-006/symbols.md'
    
    all_funcs = []
    all_classes = []
    all_mods = []

    if not os.path.exists(input_dir):
        print(f"Error: {input_dir} does not exist")
        return

    for root, dirs, files in os.walk(input_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f_src:
                        tree = ast.parse(f_src.read())
                    
                    rel_mod_path = os.path.relpath(full_path, input_dir).replace(os.sep, '.')
                    all_mods.append(f"- {rel_mod_path}:")

                    for node in tree.body:
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not node.name.startswith('_'):
                                params = []
                                for arg in node.args.args:
                                    if arg.arg != 'self' and arg.arg != 'cls':
                                        params.append(arg.arg)
                                sig = f"({', '.join(params)})"
                                all_funcs.append(f"- name: {node.name}\n  signature: {node.name}{sig}")
                        elif isinstance(node, ast.ClassDef):
                            if not node.name.startswith('_'):
                                class_name = node.name
                                all_classes.append(f"- name: {class_name}")
                                for sub in node.body:
                                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        if not sub.name.startswith('_'):
                                            params = []
                                            for arg in sub.args.args:
                                                if arg.arg != 'self' and arg.arg != 'cls':
                                                    params.append(arg.arg)
                                            sig = f"({', '.join(params)})"
                                            all_classes.append(f"  - {class_name}.{sub.name}: {class_name}.{sub.name}{sig}")
                except Exception as e:
                    print(f"Error parsing {full_path}: {e}")
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

if __name__ == "__main__":
    run()
