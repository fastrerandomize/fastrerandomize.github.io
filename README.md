# fastrerandomize

[<img src="https://img.shields.io/badge/Demo-View%20Demo-blue" alt="Demo Button">](https://cran.r-project.org/web/packages/fastrerandomize/vignettes/MainVignette.html)
[<img src="https://img.shields.io/badge/CRAN-View%20on%20CRAN-green" alt="CRAN Button">](https://cran.r-project.org/web/packages/fastrerandomize/index.html)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

An R package for hardware-accelerated rerandomization and exact randomization testing in experimental design.

## Features

- 🚀 GPU/XLA-accelerated acceptable randomization generation 
- 🔢 Supports both exact enumeration and Monte Carlo sampling
- 📉 Built-in balance metrics (Hotelling's T²) and custom threshold functions
- 📈 Randomization-based inference with fiducial intervals
- 💾 Memory-efficient, key-based batched processing for large experiments

## Installation

```r
# Install from CRAN
install.packages("fastrerandomize")

# Build Python backend (requires conda)
library(fastrerandomize)
build_backend(conda_env = "fastrerandomize")
```

## About

Package by [Rebecca Goldstein](https://rebeccasgoldstein.com/), [Connor Jerzak](https://ConnorJerzak.com), [Aniket Kamat](https://github.com/aniketkamat), and [Fucheng Warren Zhu](https://github.com/WarrenZhu050413)   

## Kernels article and audio

`kernels.html` contains the article and its generated audio player/transcript.
The spoken adaptation is maintained in `audio/kernels-narration.json`, with ten
chapters, pronunciation substitutions, and hashes identifying its written source.
Audio is generated locally with [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
(Apache-2.0 weights), [MLX Audio](https://github.com/Neywa-Labs/mlx-audio), and the
stock American English `af_heart` voice. No speech API is used by the website.

On Apple Silicon, install `uv`, `ffmpeg` (including `ffprobe`), and `espeak-ng`, then:

```sh
uv venv --python 3.12 temp/audio-venv
uv pip install --python temp/audio-venv/bin/python -r audio/requirements.txt
temp/audio-venv/bin/python audio/generate.py build
temp/audio-venv/bin/python audio/generate.py check
```

The generator reuses paragraph recordings in the ignored `temp/kernels-audio`
directory when their spoken text, model, voice, or generation settings have not
changed. It builds a normalized, mono 96 kbps MP3, measures the encoded output,
and writes the timing/version manifest before refreshing the player's transcript
and chapter links. Model weights stay in the local Hugging Face cache. Only the
finished MP3 and the small source, manifest, and generation files belong in Git.

After editing the article, review the narration for the same changes. Run
`temp/audio-venv/bin/python audio/generate.py article-hash` and update the
`article_sha256` field in the narration source after that review. `build` refuses
to use a narration source that refers to different article content. The imported
Downloads-file hash is retained separately as provenance. The generated HTML
between the `KERNELS AUDIO` comments should be regenerated rather than hand-edited.

`render` refreshes the player and transcript from an existing matching recording;
`check` verifies the source hashes, audio hash, chapter ranges, and paragraph count.
When rebuilding, also review pronunciation and audio joins, check the narration
against its transcript, and verify playback, chapter seeking, and the article's
interactive figures through a local HTTP preview. GitHub Pages serves the static
files; there is no runtime speech-generation service.
