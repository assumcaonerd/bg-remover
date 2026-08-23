# BG Remover

Desktop application for AI-powered background removal with side-by-side before/after preview.

Built with Python, [rembg](https://github.com/danielgatis/rembg), Pillow and CustomTkinter.

## Features

- Select any image (PNG, JPG, JPEG, WEBP, BMP, GIF)
- Side-by-side preview (Before / After)
- Transparent background preview with checkerboard pattern
- Export result as real PNG with transparency
- Non-blocking UI (processing runs in a background thread)

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

The first time you click **Remover Fundo**, the app may take 1–2 minutes.  
`rembg` automatically downloads the AI model (`u2net`). Subsequent runs are much faster.

## Interface

- Window size: ~920×680
- Three action buttons
- Two preview panels (380×380)
- Status bar at the bottom

Images are automatically resized to fit the preview panels while keeping aspect ratio.
