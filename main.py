#!/usr/bin/env python3
"""One Word From Your Ex — make.fun entry.

Writes exactly one word to $MAKEFUN_OUTPUT_DIR/entry.txt (default /output):
the word the entrant's ex would use to describe them. One word, no spaces,
no punctuation, no trailing newline.

Word: "refunded" — tried, found wanting, sent back for a refund.
Funny (a person returned like a defective purchase) and painfully honest
(the relationship ended because the sender did not make the cut).
"""

import os
import stat
import sys
import tempfile

WORD = "refunded"


def _write_all(fd, data):
    """Write every byte, looping over partial writes."""
    view = memoryview(data)
    while view:
        n = os.write(fd, view)
        if n == 0:
            raise OSError("short write: wrote 0 bytes")
        view = view[n:]


def _clean_output_dir(out_dir):
    """Remove the *contents* of the output dir, never the dir itself:
    the grader mounts that directory."""
    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        if os.path.isdir(path) and not os.path.islink(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(path)
        else:
            os.unlink(path)


def _validate_word(word):
    """The entry must be exactly one word: 1-24 chars, no whitespace."""
    if not word or len(word) > 24:
        raise SystemExit("entry word must be 1-24 characters")
    if any(ch.isspace() for ch in word):
        raise SystemExit("entry must be a single word with no spaces")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    _clean_output_dir(out_dir)

    _validate_word(WORD)

    data = WORD.encode("utf-8")
    final_path = os.path.join(out_dir, "entry.txt")

    for attempt in range(3):
        fd = None
        tmp_path = None
        try:
            # mkstemp inside the try: each attempt gets a unique temp file
            # (O_EXCL by construction), so a stale temp from a crashed run
            # can never collide with or be mistaken for this attempt's file.
            fd, tmp_path = tempfile.mkstemp(
                dir=out_dir, prefix=".entry.txt.", suffix=".tmp"
            )
            try:
                os.chmod(tmp_path, 0o644)
                _write_all(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
                fd = None
            os.replace(tmp_path, final_path)
            tmp_path = None  # consumed by the rename; nothing to clean up
            os.chmod(final_path, 0o644)
            break
        except OSError:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if tmp_path is not None:
                try:
                    os.unlink(tmp_path)
                except FileNotFoundError:
                    pass
            if attempt == 2:
                raise

    # Re-read and validate what actually landed on disk.
    with open(final_path, "rb") as f:
        written = f.read()
    if written != data:
        raise SystemExit("entry.txt contents do not match the entry word")
    if os.stat(final_path).st_mode & 0o777 != 0o644:
        raise SystemExit("entry.txt mode is not 0644")
    text = written.decode("utf-8")
    if text != WORD or " " in text or "\n" in text or "\t" in text:
        raise SystemExit("entry.txt is not exactly one word")
    return 0


if __name__ == "__main__":
    sys.exit(main())
