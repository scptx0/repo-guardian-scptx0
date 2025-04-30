import hashlib
import zlib
from pathlib import Path
from dataclasses import dataclass

@dataclass
class GitObject:
    obj_type: str
    size: int
    content: bytes
    sha: str

def compute_git_hash(obj_type: str, content: bytes) -> str:
    header = f"{obj_type} {len(content)}".encode()
    full_data = header + b'\x00' + content
    return hashlib.sha1(full_data).hexdigest()

def read_loose(path: Path, use_sha1=False) -> GitObject:
    """
    Lee un objeto suelto (loose) de Git y valida su hash.
    
    path: Ruta completa al archivo dentro de .git/objects/xx/yyyyyy...
    use_sha1: Si se usa SHA-1 en lugar de SHA-256
    retorna GitObject si es válido, lanza excepciones si no.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    with path.open("rb") as f:
        compressed = f.read()

    try:
        decompressed = zlib.decompress(compressed) # Bufer binario
    except zlib.error as e:
        raise ValueError(f"Error al descomprimir el objeto: {e}")

    # Extracción de cabecera
    try:
        header_end = decompressed.index(b'\x00')
        header = decompressed[:header_end].decode()
        obj_type, size_str = header.split()
        size = int(size_str)
    except Exception as e:
        raise ValueError(f"Cabecera inválida: {e}")

    if obj_type not in {"blob", "tree", "commit", "tag"}:
        raise ValueError(f"Tipo de objeto no reconocido: {obj_type}")

    # Extraccion de contenido
    content = decompressed[header_end + 1:]
    if len(content) != size:
        raise ValueError(f"Tamaño declarado ({size}) no coincide con tamaño real ({len(content)})")

    sha = compute_git_hash(obj_type, content)

    # Validar que el SHA coincide con la ruta del archivo
    expected_sha = path.parent.name + path.name
    if not sha.startswith(expected_sha):
        raise ValueError(f"SHA no coincide: esperado {expected_sha}, calculado {sha}")

    return GitObject(obj_type=obj_type, size=size, content=content, sha=sha)
