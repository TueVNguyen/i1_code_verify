import re
import ast
def _detect_callable_name(user_code: str, fn_name: str):
    """
    Returns (class_name, True) if we find 'fn_name' as a method in a class,
    (fn_name, False) if we find 'fn_name' as a top-level function,
    or (None, None) if not found.
    """
    try:
        tree = ast.parse(user_code)
    except SyntaxError:
        return (None, None)

    found_class = None
    found_function_top_level = False

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for subnode in node.body:
                if isinstance(subnode, ast.FunctionDef) and subnode.name == fn_name:
                    found_class = node.name
                    break
            if found_class:
                break
        elif isinstance(node, ast.FunctionDef) and node.name == fn_name:
            found_function_top_level = True

    if found_class:
        return (found_class, True)
    elif found_function_top_level:
        return (fn_name, False)

    return (None, None)

