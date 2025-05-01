from pathlib import Path
from guardian.object_scanner import read_loose, read_pack_with_idx
import argparse

def scan_repository(repo_path: Path):
    """
    Escanea un repositorio Git para detectar objetos corruptos.
    """
    pack_dir = repo_path / "objects/pack"
    loose_dir = repo_path / "objects"

    # Procesar packfiles
    for pack_file in pack_dir.glob("*.pack"):
        idx_file = pack_file.with_suffix(".idx")
        if not idx_file.exists():
            print(f"Índice no encontrado para {pack_file}")
            continue

        try:
            objects = read_pack_with_idx(pack_file, idx_file)
            print(f"Se procesaron {len(objects)} objetos en {pack_file}")
        except ValueError as e:
            print(f"Error procesando {pack_file}: {e}")
            if "Invalid CRC" in str(e):
                return 2  # Código de salida para CRC inválido
            return 1  # Código de salida genérico para otros errores

    # Procesar objetos sueltos
    for loose_file in loose_dir.glob("**/*"):
        if loose_file.is_file() and len(loose_file.name) == 38:
            try:
                obj = read_loose(loose_file)
                print(f"Objeto válido: {obj.sha} ({obj.obj_type})")
            except ValueError as e:
                print(f"Error procesando {loose_file}: {e}")
                return 1  # Código de salida genérico para errores en objetos sueltos

    return 0  # Código de salida para éxito


def main():
    """
    Punto de entrada para el CLI.
    """
    parser = argparse.ArgumentParser(description="Herramienta para escanear repositorios Git.")
    parser.add_argument("command", choices=["scan"], help="Comando a ejecutar")
    parser.add_argument("repo", type=str, help="Ruta al repositorio Git")

    args = parser.parse_args()

    if args.command == "scan":
        repo_path = Path(args.repo)
        if not repo_path.exists():
            print(f"El repositorio {repo_path} no existe.")
            exit(1)

        exit_code = scan_repository(repo_path)
        exit(exit_code)


if __name__ == "__main__":
    main()