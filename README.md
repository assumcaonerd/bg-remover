# BG Remover

[![CI](https://github.com/assumcaonerd/bg-remover/actions/workflows/ci.yml/badge.svg)](https://github.com/assumcaonerd/bg-remover/actions/workflows/ci.yml)

Desktop application for AI-powered background removal with side-by-side before/after preview.

Built with Python, [rembg](https://github.com/danielgatis/rembg), Pillow, CustomTkinter and tkinterdnd2.

## Features

- **Drag & Drop** – drop one or more images on the left panel
- **Batch processing** – select multiple images and process them all at once
- **Visual progress bar** – shows percentage and current file during batch
- **Copy to clipboard** – one click to copy the result
- **Multiple AI models** (u2net, isnet, birefnet, anime, portrait, etc.)
- Side-by-side preview with checkerboard transparency
- Real PNG export with transparency
- Non-blocking UI (background thread)
- Custom application icon

## Requirements

- Python 3.9+
- Dependencies in `requirements.txt`

Optional (better Windows clipboard support):
```bash
pip install pywin32
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

### Single image
1. Drag an image or click **Selecionar**
2. Choose a model (optional)
3. Click **Remover Fundo**
4. Save or **Copiar** to clipboard

### Batch (multiple images)
1. Click **Lote (várias)** or drop several files at once
2. Choose the output folder
3. A progress bar appears showing current file and percentage
4. The app processes everything automatically and saves `_sem_fundo.png` files

### First run note
The first time you use a new model it may take 1–2 minutes to download. After that it is much faster.

### Recommended models

| Use case              | Model                         |
|-----------------------|-------------------------------|
| General purpose       | u2net / isnet-general-use     |
| Fast / lightweight    | u2netp / silueta              |
| People / portraits    | u2net_human_seg / birefnet-portrait |
| Anime / illustrations | isnet-anime                   |
| High quality          | birefnet-general              |

## Interface

- Window ≈ 980×800
- Model selector + 5 action buttons
- Progress bar (visible only during batch)
- Two preview panels
- Status bar
- Drag images onto the left panel

## Building a standalone executable (PyInstaller)

### Local build

```bash
pip install -r requirements.txt pyinstaller
pyinstaller bg-remover.spec --noconfirm --clean
```

The output will be in `dist/BG-Remover/`.

Files used for packaging:
- `bg-remover.spec` – PyInstaller configuration
- `hook-tkinterdnd2.py` – collects native drag-and-drop libraries

### Automated builds (GitHub Actions)

Workflow: `.github/workflows/build.yml`

**How to trigger:**
1. Go to the **Actions** tab → **Build Executables** → **Run workflow**
2. Or create a version tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

The workflow builds for:
- **Windows** (`BG-Remover-Windows`)
- **Linux** (`BG-Remover-Linux`)

Artifacts stay available for 14 days. When you push a `v*` tag, a GitHub Release is created automatically with the zipped builds.

> Note: AI models are **not** bundled. They download automatically on first use (to the user cache), which keeps the executable smaller.

## Continuous Integration

This repository uses GitHub Actions (`.github/workflows/ci.yml`).

On every push and pull request to `main` the workflow:

- Runs on Python 3.10, 3.11 and 3.12
- Installs dependencies from `requirements.txt`
- Lints with Ruff
- Checks syntax (`py_compile` + AST)
- Runs a smoke test of the main imports (without opening the GUI)

You can see the status in the **Actions** tab of the repository.
