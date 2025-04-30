import pytest
from guardian.object_scanner import read_loose, GitObject
from pathlib import Path
import zlib

# El formato hash del subrepositorio es sha1
FIXTURES = Path("fixtures/corrupt-blob.git/objects")

def test_valid_loose_blob():
    path = FIXTURES / "ce" / "013625030ba8dba906f756967f9e9ca394464a"
    obj = read_loose(path, use_sha1=True)
    assert isinstance(obj, GitObject)
    assert obj.obj_type == "blob"
    assert obj.size == len(obj.content)
    assert obj.sha.startswith("ce0136")  # SHA comienza con el nombre del archivo


def test_nonexistent_file():
    path = FIXTURES / "00" / "doesnotexist"
    with pytest.raises(FileNotFoundError):
        read_loose(path, use_sha1=True)


def test_invalid_zlib_format(tmp_path):
    corrupted_path = tmp_path / "badobj"
    corrupted_path.write_bytes(b"not-zlib-compressed-data")
    with pytest.raises(ValueError, match="Error al descomprimir"):
        read_loose(corrupted_path, use_sha1=True)


def test_unknown_type(tmp_path):
    # Construimos un objeto zlib válido pero con tipo inválido
    content = b"foobar 10\x00hello_data"
    compressed = zlib.compress(content)
    invalid_path = tmp_path / "ff"
    invalid_path.write_bytes(compressed)
    with pytest.raises(ValueError, match="Tipo de objeto no reconocido"):
        read_loose(invalid_path, use_sha1=True)


def test_invalid_size_mismatch(tmp_path):
    # Cabecera dice size=5, pero damos 10 bytes
    content = b"blob 5\x00abcdefghij"
    compressed = zlib.compress(content)
    obj_path = tmp_path / "zz"
    obj_path.write_bytes(compressed)
    with pytest.raises(ValueError, match="Tamaño declarado"):
        read_loose(obj_path, use_sha1=True)


def test_hash_mismatch(tmp_path):
    # Creamos un objeto correcto pero lo colocamos en un path falso
    raw = b"blob 5\x00abcde"
    compressed = zlib.compress(raw)
    fake_path = tmp_path / "00" / "1234567890abcdef"
    fake_path.parent.mkdir(parents=True, exist_ok=True)
    fake_path.write_bytes(compressed)
    with pytest.raises(ValueError, match="SHA no coincide"):
        read_loose(fake_path, use_sha1=True)
