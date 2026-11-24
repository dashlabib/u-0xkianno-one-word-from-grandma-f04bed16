#!/usr/bin/env python3
"""Publish grandma's one word about AI for the make.fun bounty
"One Word From Grandma".

The word lives in ``entry.txt`` next to this file: exactly one
word, the single word a grandma would text about AI — warm, a
little baffled, tied to robots, and funny on its own with no
caption or context. This program reads that file as raw bytes,
decodes it as UTF-8, checks the word against the bounty gate
(1 to 30 characters, not only white space, exactly one word, no
punctuation tricks), and publishes the raw bytes verbatim to
``entry.txt`` in the output directory. Publishing is byte-for-byte:
``entry.txt`` carries no trailing newline, and the published file
is identical to the source file, byte for byte. After writing,
the program reads the published file back and compares bytes; a
mismatch is a hard failure.

Standard library only: no network access, no clock reads, no
randomness, so two runs always produce identical output.

The output directory is ``--output-dir`` when given, else
``$MAKEFUN_OUTPUT_DIR`` when set, else ``/output``. Pass
``--verify-only`` to check the word without writing anything.
"""

import argparse
import os
import sys
import typing
from pathlib import Path
from typing import NamedTuple


class Entry(NamedTuple):
    """One entry, kept as a pair so the two can never drift apart.

    ``raw`` is the exact bytes that get published verbatim;
    ``text`` is those bytes decoded as UTF-8, which the gate
    checks. A function that takes an ``Entry`` validates the same
    bytes it publishes.
    """

    raw: bytes
    text: str

DEFAULT_MAX_CHARS = 30
MIN_CHARS = 1
DEFAULT_OUTPUT_DIR = "/output"
ENTRY_FILENAME = "entry.txt"


def entry_path() -> Path:
    """Return the path of the entry file shipped with this program."""
    return Path(__file__).resolve().parent / ENTRY_FILENAME


def load_raw(path: Path) -> bytes:
    """Read the entry file as raw bytes, failing loudly if unreadable."""
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise SystemExit(f"entry file not found: {path}")
    except OSError as exc:
        raise SystemExit(f"cannot read entry file {path}: {exc}")


def decode(raw: bytes) -> str:
    """Decode raw entry bytes as UTF-8, keeping every byte's meaning.

    Unlike a one-line entry, a one-word entry carries no trailing
    newline to strip: the file is the word and nothing else, so
    decoding returns the text exactly as stored. Any whitespace in
    it is part of the entry and is rejected by :func:`validate`
    below, so a stray space or newline cannot slip through.
    """
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"entry is not valid UTF-8: {exc}")


def load_entry() -> Entry:
    """Read the shipped entry file and return it as an ``Entry``.

    The raw bytes are what gets published verbatim; the decoded
    text is what the gate checks. Keeping the pair together means
    no caller can validate one file and publish another.
    """
    path = entry_path()
    raw = load_raw(path)
    return Entry(raw=raw, text=decode(raw))


def fail(message: str) -> "typing.NoReturn":
    """Abort with a single clear error line on stderr (exit code 1)."""
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def shape_violations(text: str, max_chars: int) -> list:
    """Check the text's shape: length, whitespace, controls.

    These are the sealed scorer's rules, independent of what the
    word says. An empty or whitespace-only text short-circuits the
    rest: no other shape rule can be judged on nothing.
    """
    problems = []
    if not text or text.isspace():
        problems.append("entry is empty or only white space")
        return problems
    if len(text) < MIN_CHARS:
        problems.append(
            f"entry is {len(text)} characters, below the "
            f"{MIN_CHARS}-character minimum"
        )
    if len(text) > max_chars:
        problems.append(
            f"entry is {len(text)} characters, over the "
            f"{max_chars}-character limit"
        )
    if any(ch.isspace() for ch in text):
        problems.append("entry must be exactly one word, with no spaces")
    bad = [ch for ch in text if ord(ch) < 32 or ord(ch) == 127]
    if bad:
        problems.append(
            "entry must not contain control characters "
            f"(found U+{ord(bad[0]):04X})"
        )
    return problems


def word_violations(text: str) -> list:
    """Check the word reads as one grandma would text about AI.

    No punctuation tricks, no digits smuggled in as a second word,
    and no sentence hiding in the file: a single word of letters,
    the way a grandmother types it to a grandchild. It must also
    read as a real word — a vowel somewhere in it — rather than a
    keyboard mash no grandma would ever send.
    """
    problems = []
    if not text.isalpha():
        problems.append(
            "entry must be a single word of letters only "
            "(no punctuation, digits or symbols)"
        )
    elif not any(ch in "aeiouAEIOU" for ch in text):
        problems.append("entry must read as a real word (no vowel in it)")
    return problems


def gate_violations(text: str, max_chars: int) -> list:
    """Collect every way the text breaks the bounty gate, in order.

    Shape first, then word: each violation is a plain sentence
    naming the rule and the offending detail, so one run reports
    everything wrong at once instead of stopping at the first
    problem. An empty list means the text passes the gate.
    """
    return shape_violations(text, max_chars) + word_violations(text)


def validate(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> None:
    """Reject any entry that breaks the bounty gate, naming each reason."""
    problems = gate_violations(text, max_chars)
    if problems:
        fail("; ".join(problems))


def resolve_output_dir(args: argparse.Namespace) -> Path:
    """Pick the output directory: CLI flag beats env var beats default.

    A blank ``$MAKEFUN_OUTPUT_DIR`` counts as unset rather than as
    a directory named nothing, which would otherwise fail oddly
    downstream instead of falling back to ``/output``.
    """
    if args.output_dir:
        return Path(args.output_dir)
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if env_dir:
        return Path(env_dir)
    return Path(DEFAULT_OUTPUT_DIR)


def describe(entry: Entry) -> str:
    """Summarise the entry in one line for success messages.

    Characters are what the gate counts; bytes are what the file
    holds (they differ once the text leaves ASCII).
    """
    return f"{len(entry.text)} characters, {len(entry.raw)} bytes"


def publish(raw: bytes, out_dir: Path) -> tuple:
    """Write the raw entry bytes verbatim and verify them by re-reading.

    Returns ``(path_written, byte_count)``. The bytes go to a
    temporary file in the same directory first and are moved into
    place with :func:`os.replace` only after the temporary copy
    reads back identical, so a failed write can never leave a
    half-written ``entry.txt`` behind. Raises SystemExit if the
    directory cannot be created, the write fails, or the bytes read
    back do not match the bytes written. The destination is resolved
    first so a surprising ``--output-dir`` (a symlink escaping the
    intended tree, for instance) is visible in the success message
    rather than silently honoured.
    """
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SystemExit(f"cannot create output directory {out_dir}: {exc}")
    out_path = out_dir.resolve() / ENTRY_FILENAME
    tmp_path = out_path.with_name(ENTRY_FILENAME + ".tmp")
    try:
        try:
            tmp_path.write_bytes(raw)
        except OSError as exc:
            raise SystemExit(f"cannot write {tmp_path}: {exc}")
        try:
            staged = tmp_path.read_bytes()
        except OSError as exc:
            raise SystemExit(f"cannot read back {tmp_path}: {exc}")
        if staged != raw:
            raise SystemExit("staged entry does not match entry.txt")
        try:
            os.replace(tmp_path, out_path)
        except OSError as exc:
            raise SystemExit(f"cannot publish {out_path}: {exc}")
    finally:
        # A failed publish must not leave a stale temp file behind
        # for the next run (or the grader) to trip over.
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
    try:
        published = out_path.read_bytes()
    except OSError as exc:
        raise SystemExit(f"cannot read back {out_path}: {exc}")
    if published != raw:
        raise SystemExit("published entry does not match entry.txt")
    return out_path, len(published)


def parse_args(argv=None) -> argparse.Namespace:
    """Parse the command-line options for this publisher."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="directory to write entry.txt into "
        "(default: $MAKEFUN_OUTPUT_DIR or /output)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the word without writing it",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"maximum entry length in characters (default: {DEFAULT_MAX_CHARS})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print nothing on success (errors still go to stderr)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Load, validate, and publish (or just verify) the entry."""
    args = parse_args(argv)
    if args.max_chars < MIN_CHARS:
        fail(f"--max-chars must be at least {MIN_CHARS}, got {args.max_chars}")
    entry = load_entry()
    validate(entry.text, args.max_chars)
    if args.verify_only:
        if not args.quiet:
            print(f"Valid: {describe(entry)}")
        return 0
    out_path, byte_count = publish(entry.raw, resolve_output_dir(args))
    if not args.quiet:
        print(f"Wrote {describe(entry)} to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
