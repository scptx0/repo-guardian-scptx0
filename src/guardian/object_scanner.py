import struct
from typing import List
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

def parse_idx(idx_path: Path) -> list[tuple[str, int, int]]:
    """
    Parsea un archivo .idx y devuelve una lista de tuplas (SHA, offset, CRC).
    """
    with idx_path.open("rb") as f:
        data = f.read()

    if data[:4] != b'\xfftOc':
        raise ValueError("Versión de idx no soportada o corrupta")

    num_objects = struct.unpack(">I", data[1020:1024])[0]  # fanout[255]
    sha_list_offset = 8 + 256 * 4
    sha_size = 20

    sha_list = [
        data[sha_list_offset + i * sha_size: sha_list_offset + (i + 1) * sha_size].hex()
        for i in range(num_objects)
    ]

    crc_list_offset = sha_list_offset + num_objects * sha_size
    offset_list_offset = crc_list_offset + num_objects * 4

    crcs = [
        struct.unpack(">I", data[crc_list_offset + i * 4: crc_list_offset + (i + 1) * 4])[0]
        for i in range(num_objects)
    ]

    offsets = [
        struct.unpack(">I", data[offset_list_offset + i * 4: offset_list_offset + (i + 1) * 4])[0]
        for i in range(num_objects)
    ]

    return list(zip(sha_list, offsets, crcs))

def read_pack_with_idx(pack_path: Path, idx_path: Path) -> List[GitObject]:
    """
    Lee un packfile con su archivo idx. Devuelve GitObjects descomprimidos con SHA real verificado.
    """
    sha_offset_pairs = parse_idx(idx_path)

    with pack_path.open("rb") as f:
        data = f.read()

    if data[:4] != b'PACK':
        raise ValueError("Header PACK inválido")

    version, num_objects = struct.unpack(">II", data[4:12])
    if version not in {2, 3}:
        raise ValueError(f"Versión de packfile no soportada: {version}")

    objects = []
    for expected_sha, offset, expected_crc in sha_offset_pairs:
        cursor = offset

        # Leer encabezado varint
        obj_header = []
        while True:
            byte = data[cursor]
            obj_header.append(byte)
            cursor += 1
            if not (byte & 0x80):
                break

        obj_type = (obj_header[0] >> 4) & 0x07
        size = obj_header[0] & 0x0F
        shift = 4
        for b in obj_header[1:]:
            size |= (b & 0x7F) << shift
            shift += 7

        obj_type_str = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}.get(obj_type, "unknown")
        if obj_type_str == "unknown":
            raise ValueError(f"Tipo de objeto {obj_type} no soportado")

        # Descomprimir el objeto
        decompress_obj = zlib.decompressobj()
        content = bytearray()
        crc_calculator = zlib.crc32(b"")  # Inicializar CRC
        while True:
            if cursor >= len(data):
                raise ValueError("Packfile truncado o comprimido incorrectamente")
            chunk = data[cursor:cursor + 512]
            decompressed = decompress_obj.decompress(chunk)
            content.extend(decompressed)
            crc_calculator = zlib.crc32(chunk, crc_calculator)  # Actualizar CRC
            cursor += len(chunk)
            if decompress_obj.eof:
                break

        # Validar CRC
        if crc_calculator != expected_crc:
            raise ValueError(f"Invalid CRC at offset {offset}")

        actual_sha = compute_git_hash(obj_type_str, bytes(content))
        if actual_sha != expected_sha:
            raise ValueError(f"SHA no coincide en offset {offset}: esperado {expected_sha}, calculado {actual_sha}")

        obj = GitObject(obj_type=obj_type_str, size=len(content), content=bytes(content), sha=actual_sha)
        objects.append(obj)

    return objects