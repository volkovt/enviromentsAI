import os
import yaml

def _get_from_pointer(doc: dict, pointer: str):
    """
    Navega em um dicionário via JSON Pointer (ex: '/components/schemas/Foo').
    """
    parts = pointer.lstrip('/').split('/') if pointer else []
    node = doc
    for part in parts:
        node = node.get(part)
        if node is None:
            break
    return node

class OpenAPIResolver:
    """
    Carrega um arquivo OpenAPI/Swagger e resolve $refs locais e externos recursivamente.
    """
    def __init__(self):
        self._root = None

    def load(self, file_path: str) -> dict:
        base_dir = os.path.dirname(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            doc = yaml.safe_load(f)
        self._root = doc
        return self._clean_nulls(self._resolve_refs(doc, base_dir))

    def _resolve_refs(self, node, base_dir: str):
        if isinstance(node, dict):
            if '$ref' in node:
                ref = node['$ref']
                if '#' in ref:
                    ref_path, pointer = ref.split('#', 1)
                else:
                    ref_path, pointer = ref, ''
                if ref_path:
                    abs_path = os.path.join(base_dir, ref_path)
                    with open(abs_path, 'r', encoding='utf-8') as rf:
                        ext = yaml.safe_load(rf)
                    target = _get_from_pointer(ext, pointer)
                    return self._resolve_refs(target, os.path.dirname(abs_path))
                target = _get_from_pointer(self._root, pointer)
                return self._resolve_refs(target, base_dir)
            return {k: self._resolve_refs(v, base_dir) for k, v in node.items()}
        if isinstance(node, list):
            return [self._resolve_refs(item, base_dir) for item in node]
        return node

    def _clean_nulls(self, obj):
        """
        Remove recursivamente todos os valores None de dicionários e listas.
        """
        if isinstance(obj, dict):
            return {
                k: self._clean_nulls(v)
                for k, v in obj.items()
                if v is not None
            }
        elif isinstance(obj, list):
            return [self._clean_nulls(v) for v in obj if v is not None]
        else:
            return obj