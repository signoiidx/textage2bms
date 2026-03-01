# CLAUDE.md

This file describes the architecture, conventions, and development workflow for
the `textage2bms` project, intended for AI assistants working in this codebase.

## Project Overview

`textage2bms` is a single-file Python script that converts rhythm game chart
data from textage.cc into BMS (Be-Music Script) format. It does this by
launching a headless browser via Selenium to load a textage.cc chart URL,
extracting DOM content with PyQuery, computing note positions from CSS pixel
values, and writing the resulting BMS file to stdout.

The entry point is `textage2bms.py`. There are no other source modules. All
logic lives in that one file.

**Usage:**

```sh
python3 textage2bms.py 'https://textage.cc/score/24/marenect.html?1AC0' > output.bms
```

Output goes to stdout. Diagnostic messages (section numbers, skipped notes,
parse warnings) go to stderr.

## Repository Layout

```
textage2bms/
├── .github/
│   ├── dependabot.yml          # Weekly pip dependency updates
│   └── workflows/
│       └── test.yml            # CI: runs unit tests on Python 3.12 / Ubuntu
├── .githooks/
│   └── pre-commit              # Runs the full test suite before every commit
├── tests/
│   └── test_textage2bms.py    # 5 unit tests with fully mocked dependencies
├── .gitignore                  # Standard Python ignores + *.bms, *.bme output files
├── LICENSE                     # AGPLv3
├── README.md
├── requirements.txt            # selenium, pyquery (unpinned)
└── textage2bms.py              # Entire application: 241 lines
```

## Architecture

The pipeline has four stages, all driven by `main()`:

### 1. Browser launch — `get_driver()`

Tries a prioritized list of Chrome/Chromium and Firefox binary locations in
headless mode. The trial order is:

1. `chromium` at `/usr/bin/chromium` with `--headless=new`
2. `chrome` at `/usr/bin/chrome` with `--headless=new`
3. Chrome with auto-detected binary and `--headless=new`
4. `firefox` at `/usr/bin/firefox` with `-headless`
5. Firefox with auto-detected binary and `-headless`

Raises `RuntimeError` (with a consolidated error list) if every candidate
fails. Chrome uses `--headless=new` (Selenium 4 / Chrome 112+ syntax);
Firefox uses `-headless`. These flags are not interchangeable.

### 2. Metadata extraction — `build_headers(driver)`

After the page loads, runs `driver.execute_script()` to read JavaScript globals
(`genre`, `title`, `artist`, `bpm`) that textage.cc exposes. Several BMS header
fields are hard-coded: `#PLAYER 1`, `#RANK 3`, `#DIFFICULTY 4`,
`#PLAYLEVEL 12`, `#STAGEFILE`, and `#WAV02 out.wav`. There is no config file
or CLI switch for these values.

### 3. Chart parsing — `get_sections()` and `get_channels()`

- Finds every `<table cellpadding="0">` in the page. Each table is one
  measure/section of the chart.
- `get_channels(table)` reads each `<img>` inside a table. The CSS `left`
  value identifies the key lane via `CSS_LEFT_TO_CHANNEL`. The CSS `top` value
  is converted to a BMS note slot by `top_to_pos()`.
- Long Notes (LNs) are identified by the presence of `height:` in the `style`
  attribute. Their channel number is the normal channel + 40 (BMS LN
  convention). LN end positions can span section boundaries and are resolved in
  `get_sections()` via `deferring_lns_merge`.
- Sections with no `<th bgcolor="gray">` header get section number -1 and are
  renumbered to max+1 after all sections are collected.
- `compress_notes()` exists but is a no-op: it returns its input immediately,
  and the compression loop is in dead code below an unconditional `return`.

### 4. BMS output — `print_header_field()` and `print_main_data_field()`

- The header block is printed first to stdout.
- The main data block follows. Active notes encode as `AA`; silent slots as
  `00`.
- The `02` channel carries a floating-point measure ratio when a section is
  not a standard 128-unit measure.
- Channels where all values are `False` are suppressed from output.

## Key Data Structures

### `CSS_LEFT_TO_CHANNEL` (dict)

Maps CSS `left` pixel strings (e.g. `'37px'`) to BMS channel number strings
(e.g. `'11'`). This is the SP (Single Play) 7-key + scratch lane mapping.
There are exactly 8 entries:

| CSS `left` | BMS channel | Lane        |
|-----------|-------------|-------------|
| `'0px'`   | `'16'`      | Scratch     |
| `'37px'`  | `'11'`      | Key 1       |
| `'51px'`  | `'12'`      | Key 2       |
| `'65px'`  | `'13'`      | Key 3       |
| `'79px'`  | `'14'`      | Key 4       |
| `'93px'`  | `'15'`      | Key 5       |
| `'107px'` | `'18'`      | Key 6       |
| `'121px'` | `'19'`      | Key 7       |

### `LN_DISABLE` (bool, default `False`)

Global flag. Set to `True` in the source to ignore all long notes during
parsing. There is no command-line switch; the file must be edited directly.

### Section list format

Each section is `[section_num, channels_dict]`. The `channels_dict` maps a
channel string to either a `list[bool]` (note slots, 128 entries for a standard
measure) or a `float` (the `02` measure ratio for non-standard measure lengths).
Section numbers start from whatever textage.cc assigns, not necessarily 0 or 1.

## Development Setup

### Prerequisites

- Python 3.12 (matches CI)
- Chrome/Chromium or Firefox installed on the system — required for real
  execution; **not** required to run the test suite
- pip packages from `requirements.txt`

### Installation

```sh
pip install -r requirements.txt
git config core.hooksPath .githooks
```

The second command activates the pre-commit hook. Without it, commits will
not trigger the test suite locally (CI will still catch failures).

### Running the tool

```sh
python3 textage2bms.py 'https://textage.cc/score/24/marenect.html?1AC0' > output.bms
```

Stderr will contain diagnostic lines (pixel positions, skipped LNs, section
renumbering). These are informational and do not affect the BMS output.

Generated `*.bms` and `*.bme` files are git-ignored.

## Testing

### Run the test suite

```sh
python3 -m unittest discover -s tests -v
```

This is identical to the CI command and what the pre-commit hook runs.

### Test structure

All five tests live in `tests/test_textage2bms.py`. The file stubs out both
`selenium` and `pyquery` at the `sys.modules` level before importing
`textage2bms`, so no browser installation is required to run tests.

| Test | What it covers |
|------|----------------|
| `test_build_headers_reads_expected_scripts` | Verifies `build_headers` calls `execute_script` with the correct JS expressions and maps results to the right header keys |
| `test_print_main_data_field_skips_empty_channels` | Verifies channels with all-`False` notes are omitted from output; non-list `02` values (measure ratio) are printed directly |
| `test_main_runs_pipeline_and_quits_driver` | Integration: verifies `main()` calls each stage in order and always calls `driver.quit()` |
| `test_main_quits_driver_on_error` | Verifies `driver.quit()` is called even when an exception is raised during processing |
| `test_main_requires_url_argument` | Verifies `main()` raises `SystemExit` when no URL argument is given |

### Adding tests

- New tests belong in `tests/test_textage2bms.py` or a new file in `tests/`.
- When testing functions that use `pq(...)` directly (e.g. `get_channels`,
  `get_sections`), mock `textage2bms.pq` rather than the `pyquery` module
  itself, because the module-level stub replaces `PyQuery` with a lambda
  returning `None`.
- The existing stub approach (`sys.modules.setdefault`) means test files must
  install stubs before `import textage2bms`. Follow the same pattern.

## Code Conventions

- **Naming**: `snake_case` for all functions and local variables; `ALL_CAPS`
  for module-level constants (`LN_DISABLE`, `CSS_LEFT_TO_CHANNEL`).
- **Error handling**: Bare `except` clauses are intentional in parse loops
  (`get_channels`, `get_sections`). They log to stderr and continue, treating
  unrecognised note elements as recoverable. Do not convert these to broad
  `except Exception` or narrow typed catches without understanding which
  specific exceptions occur in practice.
- **stderr vs stdout**: All diagnostic and warning output uses
  `print(..., file=stderr)`. Stdout is exclusively for BMS file content.
  Any `print()` without `file=stderr` will corrupt the BMS output when the
  tool is used with shell redirection (`> output.bms`).
- **PyQuery alias**: `from pyquery import PyQuery as pq`. Within the code,
  `pq(element)` wraps a raw DOM element into a queryable object and
  `pq(html_string)` parses an HTML string. Both patterns appear in the same
  file.
- **Dead code**: The `compress_notes` function body after the first `return`
  is dead. It is preserved as a comment block showing the intended future
  implementation. Do not delete it without understanding the intent.
- **Hard-coded BMS values**: `#PLAYER`, `#RANK`, `#DIFFICULTY`, `#PLAYLEVEL`,
  `#STAGEFILE`, and `#WAV02` are hard-coded in `build_headers`. There is no
  configuration file or CLI for these.

## Known Limitations and Issues

### LN (Long Note) support has known bugs

Long note end-position resolution in `get_sections` has correctness issues. The
`deferring_lns_merge` logic that places LN endpoints into adjacent sections can
produce wrong results. If working on LN-related code, read `get_sections` and
`get_channels` together before making changes. `LN_DISABLE = True` (edit the
source) is available as a workaround for users who do not need LNs.

### `compress_notes` is disabled

The function immediately returns its input. The compression algorithm (reducing
note slot arrays by a power-of-2 factor when sparseness allows) is commented
out below. This means note data in BMS output is always at full resolution
(128 slots per standard measure), which produces larger but always-correct
output. Do not re-enable the compression loop without writing tests that cover
its edge cases.

### DP (Double Play) is not supported

`CSS_LEFT_TO_CHANNEL` only covers the SP (Single Play) layout. There is no
mapping for the second player's lanes. Attempting to convert a DP chart will
silently drop the second-side notes.

### No BPM change or SOF-LAN support

BPM change events on the chart are logged to stderr as "BPM change?" and
skipped. SOF-LAN (speed changes) are not handled.

### `top_to_pos` contains magic number corrections

The function applies four hard-coded `if pos == N: pos = N+1` corrections
(for values 10, 42, 74, 106). These are off-by-one adjustments for specific
pixel-to-slot boundaries. The origin of these values is not documented; do not
remove them without verifying against real textage.cc chart data.

### Section number offset

`print_main_data_field` formats section numbers zero-padded to three digits.
The section numbering starts from the first section on the page minus 1
(`offset = sections[0][0] - 1`), so output does not always start at `#001`.
Verify with actual chart pages when working on section numbering.

## Areas to Be Careful About

### `driver.quit()` must always be called

The `try/finally` in `main()` ensures `driver.quit()` runs even on exceptions.
If refactoring `main()` or extracting the pipeline into helper functions, do
not break this guarantee. The `test_main_quits_driver_on_error` test enforces
this contract.

### CSS pixel values are exact strings

The `CSS_LEFT_TO_CHANNEL` keys (`'0px'`, `'37px'`, etc.) must match the exact
string values in textage.cc's rendered HTML. If textage.cc changes its layout,
the mapping silently breaks: notes with unrecognised `left` values produce a
`KeyError` caught by the bare `except`, and those notes are dropped with a
stderr log. Check this mapping first if notes go missing.

### LN channel arithmetic

LN channels are computed as `int(CSS_LEFT_TO_CHANNEL[key]) + 40`. This means
the scratch LN channel is `56` (16+40) and key channels go from `51` to `59`.
The end-removal line removes the source-note entry from the normal channel so
the note does not appear as both an LN and a regular note.

### Selenium headless flag syntax

Chrome uses `--headless=new`; Firefox uses `-headless`. If a future Selenium or
browser update changes these flags, `get_driver` will silently exhaust all
candidates and raise `RuntimeError`. Check this function first if the tool
fails to launch a browser.

## CI/CD

- **GitHub Actions** (`.github/workflows/test.yml`): triggers on every push
  and pull request; runs `python -m unittest discover -s tests -v` on Python
  3.12 / ubuntu-latest. No browser is installed in CI because tests mock all
  browser interactions.
- **Dependabot** (`.github/dependabot.yml`): opens weekly PRs to update pip
  dependencies (`selenium`, `pyquery`). Review these PRs for breaking changes
  in Selenium's API, particularly around `Options` and `WebDriver` constructor
  signatures.
- **Pre-commit hook** (`.githooks/pre-commit`): runs the same test command
  using `set -eu`, so any test failure blocks the commit. Activate with
  `git config core.hooksPath .githooks`.

## Fork Lineage

This project is a fork chain:

1. **Saren-Arterius/textage2bms** — original
2. **16iro/textage2bms** — added SOF-LAN and charge notes spanning multiple bars
3. **signoiidx/textage2bms** (current) — stripped to a single file, added
   headless browser support, Selenium 4 compatibility, and the test suite

Features from fork 2 (SOF-LAN, charge notes) are not present in the current
codebase. The LN code that does exist originates from that lineage.
