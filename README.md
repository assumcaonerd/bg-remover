# BG Remover

Desktop application for AI-powered background removal with side-by-side before/after preview.

Built with Python, [rembg](https://github.com/danielgatis/rembg), Pillow, CustomTkinter and tkinterdnd2.

## Features

- **Drag & Drop** support – drop an image directly on the preview panel
- **Multiple AI models** to choose from (u2net, isnet, birefnet, anime, portrait, etc.)
- Side-by-side preview (Before / After)
- Transparent background preview with checkerboard pattern
- Export result as real PNG with transparency
- Non-blocking UI (processing runs in a background thread)
- Custom application icon

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

### First run note

The first time you process an image with a new model, the app may take 1–2 minutes.  
`rembg` automatically downloads the selected AI model. Subsequent runs with the same model are much faster.

### Recommended models

| Use case              | Model                    |
|-----------------------|--------------------------|
| General purpose       | u2net / isnet-general-use |
| Fast / lightweight    | u2netp / silueta         |
| People / portraits    | u2net_human_seg / birefnet-portrait |
| Anime / illustrations | isnet-anime              |
| High quality          | birefnet-general         |

## Interface

- Window size: ~960×720
- Model selector + three action buttons
- Two preview panels
- Status bar at the bottom
- Drag any image onto the left panel

Images are automatically resized to fit the preview panels while keeping aspect ratio.
