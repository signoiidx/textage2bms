# textage2bms

A script to convert chart data from [textage.cc](https://textage.cc) into BMS files.

## Development

- This project is maintained with OpenAI Codex-assisted development.

## Fork history

- original: [Saren-Arterius/textage2bms](https://github.com/Saren-Arterius/textage2bms)
- first fork: [16iro/textage2bms](https://github.com/16iro/textage2bms)
  - Applied SOF-LAN and Charge Notes over 2 bars.
- second fork: [signoiidx/textage2bms](https://github.com/signoiidx/textage2bms)
  - Remove unwanted files (only keep `textage2bms.py`)
  - Still there will be more...

## Current project changes

- Run in headless mode and try Chrome/Firefox WebDriver candidates automatically.

## Dependencies

- Python 3
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
