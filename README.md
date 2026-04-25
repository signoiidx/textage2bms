# textage2bms

A script to convert chart data from [textage.cc](https://textage.cc) into BMS files.

## Development

- This project is maintained with OpenAI Codex and Claude Code-assisted development.
- Unit tests and pylint checks are enforced by GitHub Actions CI.

### CI

| Workflow | Trigger | What it runs |
| --- | --- | --- |
| Pytest | push | `python -m unittest discover -s tests -v` on Python 3.12 |
| Pylint | push | `pylint $(git ls-files '*.py')` on Python 3.10–3.13 |

## Fork history

- original: [Saren-Arterius/textage2bms](https://github.com/Saren-Arterius/textage2bms)
- first fork: [16iro/textage2bms](https://github.com/16iro/textage2bms)
  - Applied SOF-LAN and Charge Notes over 2 bars.
- second fork: [signoiidx/textage2bms](https://github.com/signoiidx/textage2bms)
  - Stripped to a single file (`textage2bms.py`)
  - Added headless browser support and Selenium 4 compatibility
  - Added unit test suite and GitHub Actions CI (pytest + pylint)

## Current project changes

- Runs in headless mode; tries Chrome/Chromium and Firefox WebDriver candidates automatically.
- Unit test suite with fully mocked dependencies (no browser required to run tests).
- Pylint-clean codebase across Python 3.10–3.13.

## Dependencies

- Python 3.10-3.13
- Selenium
- Chrom{e, ium} or Firefox
- PyQuery

## Usage

`$ python3 textage2bms.py 'https://textage.cc/score/24/marenect.html?1AC0' > marenect.bms`

## Options

- `LN_DISABLE` = `[True/False]` to disable handling of LN (`textage2bms.py`)

## Not supported

- DP

## Known issues

- LN support is wacky (still)
