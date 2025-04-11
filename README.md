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
