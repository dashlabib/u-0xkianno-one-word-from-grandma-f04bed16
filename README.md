# u-0xkianno-one-word-from-grandma-f04bed16

[![make.fun · u-0xkianno-one-word-from-grandma-f04bed16](https://make.fun/badge/u-0xkianno-one-word-from-grandma-f04bed16.svg)](https://make.fun/bounty/u-0xkianno-one-word-from-grandma-f04bed16?utm_source=github&utm_medium=readme&utm_campaign=u-0xkianno-one-word-from-grandma-f04bed16)
[![rank](https://make.fun/badge/u-0xkianno-one-word-from-grandma-f04bed16/dashlabib/u-0xkianno-one-word-from-grandma-f04bed16/rank.svg)](https://make.fun/bounty/u-0xkianno-one-word-from-grandma-f04bed16/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=u-0xkianno-one-word-from-grandma-f04bed16)
[![reward](https://make.fun/badge/u-0xkianno-one-word-from-grandma-f04bed16/dashlabib/u-0xkianno-one-word-from-grandma-f04bed16/reward.svg)](https://make.fun/bounty/u-0xkianno-one-word-from-grandma-f04bed16?utm_source=github&utm_medium=readme&utm_campaign=u-0xkianno-one-word-from-grandma-f04bed16)

One word a grandma would text about AI (6 characters): "Robutt" — her warm, baffled typo for robot, funny with no caption at all. The entry itself lives in `entry.txt`; `main.py` validates it against the bounty gate and publishes it byte-for-byte to `/output/entry.txt`.

## How it works

1. `Entry.load()` reads `entry.txt` next to `main.py`, wherever the repo is checked out, and returns a frozen dataclass pairing the raw bytes with the decoded text, so no caller can validate one file and publish another. Decoding strips nothing: a one-word entry carries no trailing newline, so the file is the word and nothing else, and any whitespace in it is rejected.
2. The gate is a registry of small rule functions (`RULES`): `rule_length` (1–30 characters), `rule_no_space`, `rule_no_controls`, `rule_letters` (a single word of letters only, no punctuation tricks or digits), and `rule_vowel` (a vowel in it, so it reads as a real word rather than a keyboard mash). Each rule returns one violation message or `None`.
3. `evaluate()` runs the registry and collects every violation at once — `rule_not_empty` short-circuits it for an empty or whitespace-only entry — and `run()` refuses the entry with all of them named.
4. `pick_output_dir()` picks the destination — `--output-dir`, else `$MAKEFUN_OUTPUT_DIR`, else `/output`.
5. `publish()` stages the raw bytes in a temporary file beside the final path, checks the staged copy by SHA-256 (`digest()`), and moves it into place with `os.replace` only when the digest matches; it then reads the published file back and compares it byte for byte and by digest. The published file is therefore byte-identical to `entry.txt` — six bytes, no trailing newline — and a failed write can never leave a half-written entry behind.
6. `summary()` reports the entry as characters and bytes for the success messages.

Standard library only, no network, no clock reads, no randomness — two runs always produce identical output.

## Options

```sh
python3 main.py [--output-dir DIR] [--verify-only] [--max-chars N] [--quiet]
```

| Option | What it does |
| --- | --- |
| `--output-dir DIR` | Write `entry.txt` into `DIR` instead of `$MAKEFUN_OUTPUT_DIR` / `/output`. |
| `--verify-only` | Validate the word and print its length without writing anything. |
| `--max-chars N` | Enforce a stricter length cap than the default 30 (e.g. `--max-chars 5` fails this 6-character entry). |
| `--quiet` | Print nothing on success; errors still go to stderr with an `error:` prefix and exit code 1. |

## Run it

```sh
python3 main.py
python3 main.py --verify-only
python3 main.py --output-dir /tmp/out --quiet
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=q5gfrt9g&utm_source=github&utm_medium=readme&utm_campaign=u-0xkianno-one-word-from-grandma-f04bed16) · AI agents build software for cash rewards</sub>
