"""Publish complete PNGs during multi-stage pack builds."""
import os
from pathlib import Path
import tempfile


def save_png(image, path):
    path = Path(path)
    # Keep staging files outside the installable pack, even during a build.
    staging = path.parent.parent / 'output' / 'pack-build-tmp'
    staging.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.stem + '-', suffix='.png', dir=staging)
    try:
        with os.fdopen(fd, 'wb') as stream:
            image.save(stream, format='PNG')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)
