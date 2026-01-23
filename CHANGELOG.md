# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-01-23

### Added
- Integration icon for HACS and Home Assistant UI
- Calendar Events sensor showing upcoming daycare events
- Calendar events available as sensor attributes (next 10 events)

### Changed
- Refactored internal data structure to support calendar alongside kid data

## [1.0.0] - 2026-01-23

### Added
- Initial release
- Sleep tracking sensors (status, count, duration, last sleep)
- Feeding sensors (bottle count, volume, last bottle, last food)
- Diaper sensors (total, wet, BM, last diaper)
- Activity sensor with recent activities as attributes
- Config flow with credential validation
- Reauth flow for expired credentials
- Options flow for configurable update interval (5-120 minutes)
- Parallel API calls for improved performance
- Request timeouts for reliability
- Entity availability handling
- Proper sensor state classes for Home Assistant statistics
- HACS compatible structure
