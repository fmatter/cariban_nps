from pathlib import Path
from shutil import copy, copytree

try:
    from importlib.resources import files  # pragma: no cover
except ImportError:  # pragma: no cover
    from importlib_resources import files  # pragma: no cover

WEB_DIR = "."

data_path = Path("./data/audio")
if not data_path.is_dir():
    data_path.mkdir(parents=True)
# data_path.mkdir()
audio_path = Path("../../../../data/audio")
for f in audio_path.iterdir():
    if f.suffix != ".wav":
        continue
    if f.stem not in """{{cookiecutter.content}}""":
        continue
    new = data_path / f.name
    if not new.is_file():
        print(f"copying {f}")
        copy(f, new)

# data_path = Path("./data")
# image_path  = Path("../../../../data/")
# for f in image_path.iterdir():
#     if f.suffix != ".svg":
#         continue
#     new = data_path / f.name
#     if not new.is_file():
#         print(f"copying {f}")
#         copy(f, new)
