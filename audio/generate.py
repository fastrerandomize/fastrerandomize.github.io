#!/usr/bin/env python3
"""Build the checked-in narration and player. See the root README."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
SOURCE = AUDIO / "kernels-narration.json"
MANIFEST = AUDIO / "kernels-manifest.json"
ARTICLE = ROOT / "kernels.html"
CACHE = ROOT / "temp" / "kernels-audio"
START = "<!-- KERNELS AUDIO START -->"
END = "<!-- KERNELS AUDIO END -->"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def article_digest() -> str:
    from bs4 import BeautifulSoup, NavigableString

    soup = BeautifulSoup(ARTICLE.read_text(), "html.parser")
    # Bibliographic references remain in the written article, outside the narration.
    sections = soup.select(".kp > section:not(#references)")
    for section in sections:
        section.attrs.pop("id", None)
        for node in list(section.descendants):
            if isinstance(node, NavigableString) and not node.strip():
                node.extract()
    return digest("\n".join(str(s) for s in sections).encode())


def read_source() -> dict:
    source = json.loads(SOURCE.read_text())
    ids = [chapter["id"] for chapter in source["chapters"]]
    assert len(ids) == len(set(ids)) == 10, "Expected ten unique chapters"
    assert all(c["paragraphs"] and all(p.strip() for p in c["paragraphs"])
               for c in source["chapters"]), "Empty narration paragraph"
    assert source["article_sha256"] == article_digest(), (
        "Article changed. Review the narration before updating article_sha256."
    )
    return source


def spoken(text: str, source: dict) -> str:
    substitutions = source["pronunciations"]
    pattern = r"(?<!\w)(" + "|".join(
        re.escape(k) for k in sorted(substitutions, key=len, reverse=True)
    ) + r")(?!\w)"
    return re.sub(pattern, lambda m: substitutions[m.group(0)], text)


def probe(path: Path) -> dict:
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(path)
    ], text=True))


def loudness(path: Path) -> dict:
    result = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-af",
        "loudnorm=I=-19:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"
    ], capture_output=True, text=True, check=True)
    return json.loads("{" + result.stderr.rsplit("{", 1)[1].split("}", 1)[0] + "}")


def atomic_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def build() -> None:
    import mlx.core as mx
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model

    source = read_source()
    CACHE.mkdir(parents=True, exist_ok=True)
    versions = {name: importlib.metadata.version(name) for name in [
        "mlx-audio", "mlx", "misaki", "soundfile", "numpy", "en-core-web-sm"
    ]}
    settings = {key: source[key] for key in [
        "model", "model_revision", "voice", "speed", "sample_rate"
    ]}
    settings["versions"] = versions
    settings["join_version"] = 1
    model = None
    sr = source["sample_rate"]
    chapters = []
    paragraphs = []
    samples_written = 0
    master = CACHE / "kernels-master.wav"
    with sf.SoundFile(master, mode="w", samplerate=sr, channels=1, subtype="PCM_24") as output:
        for chapter_index, chapter in enumerate(source["chapters"]):
            chapter_start = samples_written / sr
            for paragraph_index, paragraph in enumerate(chapter["paragraphs"]):
                text = spoken(paragraph, source)
                cache_key = digest(json.dumps([text, settings], sort_keys=True).encode())
                cached = CACHE / (cache_key + ".wav")
                if not cached.exists():
                    if model is None:
                        print("Loading pinned Kokoro model", flush=True)
                        model = load_model(source["model"], revision=source["model_revision"])
                    mx.random.seed(int(cache_key[:8], 16))
                    parts = []
                    for result in model.generate(text=text, voice=source["voice"],
                                                 speed=source["speed"], lang_code="a"):
                        part = np.asarray(result.audio).reshape(-1).astype(np.float32)
                        assert part.size and np.isfinite(part).all(), "Invalid generated audio"
                        parts.append(part)
                    assert parts, "No speech generated"
                    signal = np.concatenate(parts)
                    fade = min(int(sr * .005), len(signal) // 2)
                    signal[:fade] *= np.linspace(0, 1, fade)
                    signal[-fade:] *= np.linspace(1, 0, fade)
                    sf.write(cached, signal, sr, subtype="PCM_24")
                signal, cached_sr = sf.read(cached, dtype="float32")
                assert cached_sr == sr and signal.ndim == 1 and signal.size
                paragraph_start = samples_written / sr
                output.write(signal)
                samples_written += len(signal)
                paragraphs.append({
                    "chapter": chapter["id"], "index": paragraph_index,
                    "start": round(paragraph_start, 6), "end": round(samples_written / sr, 6),
                    "text": paragraph, "speech_sha256": digest(text.encode()),
                    "cache_key": cache_key
                })
                pause = np.zeros(int(sr * .28), dtype=np.float32)
                output.write(pause)
                samples_written += len(pause)
                print(f'{chapter_index + 1}/10 {chapter["id"]} '
                      f'{paragraph_index + 1}/{len(chapter["paragraphs"])} '
                      f'({samples_written / sr:.1f}s total)', flush=True)
            chapters.append({
                "id": chapter["id"], "title": chapter["title"],
                "start": round(chapter_start, 6), "end": round(samples_written / sr, 6)
            })
            if chapter_index + 1 < len(source["chapters"]):
                pause = np.zeros(int(sr * .7), dtype=np.float32)
                output.write(pause)
                samples_written += len(pause)
    print("Normalizing and encoding MP3", flush=True)
    measured = loudness(master)
    normalization = (
        "loudnorm=I=-19:TP=-1.5:LRA=7:linear=true:"
        f'measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}:'
        f'measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}:'
        f'offset={measured["target_offset"]}'
    )
    encoded = CACHE / "kernels.mp3"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(master), "-af", normalization, "-ar", str(sr), "-ac", "1",
        "-c:a", "libmp3lame", "-b:a", "96k", "-write_xing", "1",
        "-metadata", "title=Inside the kernels", "-metadata", "artist=FastRerandomize",
        "-metadata", "comment=Full audio adaptation; AI narration with Kokoro af_heart",
        str(encoded)
    ], check=True)
    stats = probe(encoded)
    post_encode = loudness(encoded)
    assert float(post_encode["input_tp"]) < -1.5, "Encoded true peak exceeds target"
    assert abs(float(post_encode["input_i"]) + 19) < 1, "Unexpected integrated loudness"
    target = AUDIO / "kernels.mp3"
    target.write_bytes(encoded.read_bytes())
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "narration_sha256": digest(SOURCE.read_bytes()),
        "article_sha256": source["article_sha256"],
        "imported_source_sha256": source["source_sha256"],
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "settings": settings, "audio_file": "audio/kernels.mp3",
        "audio_sha256": digest(target.read_bytes()), "bytes": target.stat().st_size,
        "duration": float(stats["format"]["duration"]),
        "sample_rate": sr, "channels": 1, "bitrate": 96000,
        "loudness_lufs": float(post_encode["input_i"]),
        "true_peak_dbtp": float(post_encode["input_tp"]),
        "chapters": chapters, "paragraphs": paragraphs
    }
    atomic_json(MANIFEST, manifest)
    render()
    check()


def stamp(seconds: float) -> str:
    value = int(seconds)
    return f"{value // 60}:{value % 60:02d}"


def read_manifest(source: dict) -> dict:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["narration_sha256"] == digest(SOURCE.read_bytes()), "Narration changed; rebuild audio"
    assert manifest["article_sha256"] == article_digest(), "Narration is out of date"
    return manifest


def render() -> None:
    source = read_source()
    manifest = read_manifest(source)
    panel = f'''{START}
<div class="audio-panel" aria-labelledby="listen-title">
  <h2 id="listen-title">Listen to this article</h2>
  <p class="audio-meta">{stamp(manifest["duration"])} &middot; Audio narration</p>
  <audio id="kernels-audio" controls preload="none" aria-label="Inside the kernels, full audio adaptation">
    <source src="audio/kernels.mp3" type="audio/mpeg">
    <a href="audio/kernels.mp3">Download the audio version</a>.
  </audio>
  <div class="audio-actions">
    <label class="audio-speed" hidden>Playback speed
      <select id="audio-speed"><option value="0.75">0.75&times;</option><option value="1" selected>1&times;</option><option value="1.25">1.25&times;</option><option value="1.5">1.5&times;</option><option value="2">2&times;</option></select>
    </label>
    <a href="audio/kernels.mp3" download="inside-the-kernels.mp3">Download MP3 <span class="audio-size">({manifest["bytes"] / 1_000_000:.1f} MB)</span></a>
  </div>
  <p id="audio-status" class="audio-status" role="status" hidden></p>
</div>
{END}'''
    text = ARTICLE.read_text()
    if START in text:
        assert text.count(START) == text.count(END) == 1
        first = text.index(START)
        last = text.index(END, first) + len(END)
        text = text[:first] + panel + text[last:]
    else:
        anchor = '<h1>Inside the kernels</h1>\n</div>'
        assert text.count(anchor) == 1
        text = text.replace(anchor, anchor + "\n" + panel, 1)
    ARTICLE.write_text(text)


def check() -> None:
    source = read_source()
    manifest = read_manifest(source)
    mp3 = ROOT / manifest["audio_file"]
    assert digest(mp3.read_bytes()) == manifest["audio_sha256"]
    assert manifest["duration"] > 0 and mp3.stat().st_size < 40_000_000
    previous_end = 0
    for chapter in manifest["chapters"]:
        assert previous_end <= chapter["start"] < chapter["end"] <= manifest["duration"]
        previous_end = chapter["end"]
    assert len(manifest["paragraphs"]) == sum(len(c["paragraphs"]) for c in source["chapters"])
    print(f'Checked {len(source["chapters"])} chapters; {stamp(manifest["duration"])}; '
          f'{mp3.stat().st_size / 1_000_000:.1f} MB; '
          f'{manifest["loudness_lufs"]} LUFS; {manifest["true_peak_dbtp"]} dBTP', flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "render", "check", "article-hash"])
    args = parser.parse_args()
    {"build": build, "render": render, "check": check,
     "article-hash": lambda: print(article_digest())}[args.command]()
