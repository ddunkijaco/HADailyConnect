# Changelog

All notable changes to this project will be documented in this file.

## [2.0.2] - 2026-01-23

### Fixed
- Critical: Fixed double response body read in API that caused empty data for user info, kid summary, and kid status endpoints

## [2.0.1] - 2026-01-23

### Fixed
- Bottle volume sensor now uses valid unit `fl. oz.` instead of `oz` for volume device class

## [2.0.0] - 2026-01-23

### Added
- **Binary Sensor Platform**: Added "Sleeping" binary sensor for each child with dynamic icon (sleep/sleep-off)
- **Calendar Platform**: Proper CalendarEntity implementation for native Home Assistant calendar integration
- **Image Platform**: Latest activity photo display for each child with caching
- **Diagnostics Support**: Added diagnostics endpoint for easier troubleshooting
- **Photo Support**: API method to fetch activity photos (full size and thumbnail)
- **Retry Logic**: Exponential backoff (2s, 4s, 8s) for API calls to handle transient network failures
- **Response Validation**: Type and null checking on all API responses
- **Photo ID tracking**: Activity sensor now includes photo_id in attributes when photos are available

### Changed
- **Modernized Sensor Pattern**: Refactored all sensors to use SensorEntityDescription pattern (HA best practice)
- **Better Error Handling**: Replaced `assert` with proper error flow in config flow
- **Specific Exceptions**: Replaced broad exception handling with targeted catches (ValueError, KeyError, ClientError)
- **Enhanced CSRF Error Messages**: More detailed logging when token extraction fails
- **Calendar Device Info**: Calendar entities now properly grouped under "DailyConnect Account" device
- **Improved Logging**: Added response previews and better error context throughout

### Fixed
- **Critical**: Removed unsafe `assert` statement that could break with Python optimization (-O flag)
- **Critical**: Added proper session cleanup on authentication failures
- **Critical**: API responses now validated before processing to prevent crashes
- **Security**: Better error messages for CSRF token failures with sanitized response previews

### Technical Improvements
- Added async retry wrapper with configurable backoff
- Extended API client with comprehensive photo fetching
- Modernized entity descriptions with Callable value functions
- Added proper device grouping for all entity types
- Improved coordinator data structure validation

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
