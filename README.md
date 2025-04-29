# Repo-Guardian

**Repo-Guardian** es un proyecto de desarrollo de software avanzada cuyo resultado será una utilidad de línea de comandos (CLI) y  terminal user interface (TUI) capaz de **auditar, reparar y re-lineralizar la integridad de cualquier directorio `.git`**, ya contenga
objetos sueltos ("loose") o empaquetados en packfiles. El programa implementará:  

* **Árbol de Merkle** y verificación criptográfica con **SHA-256** (opcionalmente SHA-1 para retro-compatibilidad).  
* **Búsqueda binaria de commits defectuosos** usando `git bisect` embebido y heurísticas propias.  
* **Reconstrucción de historiales potencialmente re-escritos** (caso `git filter-repo`, `git rebase -i`, force-push, etc.) mediante cálculo del **Jaro–Winkler distance** (umbral ≥ 0,92) sobre las rutas `commit → root`.  
* **Exportación de un grafo dirigido acíclico (DAG)**; se generará `recovered.graphml` para su inspección en  Graphviz.  
* Interfaz TUI (curses) con paneles de progreso, resumen de hallazgos y comandos de reparación interactiva.  

## Badges

[![Work in Progress](https://img.shields.io/badge/Work_in_Progress-yellow)](https://img.shields.io)
[![License](https://img.shields.io/github/license/scptx0/repo-guardian)](https://github.com/usuario/repo-guardian/blob/main/LICENSE)

## Tabla de comandos útiles

| Comando                  | Descripción                                          |
|--------------------------|------------------------------------------------------|
| `ruff check .`            | Corre el linter usando **Ruff** para verificar el código. |
| `pytest`                 | Ejecuta los tests usando **pytest**.                 |
| `pytest -n <num>`        | Corre los tests en paralelo con **pytest-xdist**.    |
| `behave`                 | Ejecuta los tests de comportamiento con **Behave**.  |
| `coverage run`           | Corre los tests y genera el reporte de cobertura.    |

## Instalación

1. **Clona el repositorio**:
    ```bash
    git clone https://github.com/usuario/repo-guardian.git
    cd repo-guardian
    ```

2. **Instala las dependencias del sistema pipx**:
    Si no tienes las dependencias instaladas, usa `pipx`:
    ```bash
    pipx install ruff pytest behave coverage
    pipx inject pytest pytest-xdist
    ```
3. **Instala las dependencias del entorno virtual**:
    Si no tienes las dependencias instaladas, usa `pip`, activando antes el entorno virtual:
    ```bash
    pip install -r requirements.txt
    ``` 
