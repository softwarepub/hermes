<!--
SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)

SPDX-License-Identifier: CC0-1.0
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project tries to adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.1] - 2026-01-12

### Added

- Added ADR for `init` plugin (#324)

### Fixed

- Broken HERMES DOI in marketplace plugin metadata (#326)
- hermes init fails with cryptic error message in non-git directory (#308)
- Make --initial deposits work on Rodare (#348)
- Fix GitHub link in docs (#319)
- `hermes init` cancellation should remove created files (#328)
- `pyproject.toml` compliance with PEP 621 (#347)
- Improve marketplace visibility (#426)

### Changed

- Update poetry to more recent version. (#347)

### Security

- Patch raw logging of '-O' values that could have included arbitrary secrets. (https://github.com/softwarepub/hermes/security/advisories/GHSA-jm5j-jfrm-hm23)

## [0.9.0] - 2025-02-26

### Added

- Added the hermes init subcommand

### Fixed

- Fixes multiple bugs

### Changed

- Refactored plugin system further

## [0.8.1] - 2024-08-13

### Added

- Integrated pyproject.toml plugin into the publication process

### Changed

- Improved logging output for better error dissemination