# DailyConnect Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration to track your child's daycare activities from [DailyConnect](https://www.dailyconnect.com/).

## Features

- **Sleep Tracking**: Sleep status, count, duration, and last sleep time
- **Binary Sleep Sensor**: Visual on/off indicator when your child is sleeping
- **Feeding Tracking**: Bottle count, volume, last bottle, and last food time
- **Diaper Tracking**: Total diapers, wet diapers, BM diapers, and last diaper time
- **Activity Feed**: Recent activities from the daycare with photo support
- **Photo Display**: View the latest activity photo for each child
- **Calendar Integration**: Native Home Assistant calendar showing upcoming daycare events
- **Diagnostics**: Built-in diagnostics for easier troubleshooting
- **Robust Error Handling**: Automatic retry with exponential backoff for network issues

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add `https://github.com/ddunkijaco/HADailyConnect` with category "Integration"
5. Click "Add"
6. Search for "DailyConnect" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `dailyconnect` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for "DailyConnect"
4. Enter your DailyConnect email and password

### Options

After setup, you can configure:
- **Update interval**: How often to fetch data (5-120 minutes, default: 30)

## Sensors

For each child, the following sensors are created:

| Sensor | Description | Unit |
|--------|-------------|------|
| Sleep Status | Current sleep state (sleeping/awake) | - |
| Sleep Count | Number of naps today | naps |
| Sleep Duration | Total sleep time today | minutes |
| Last Sleep | Time of last sleep | timestamp |
| Bottle Count | Number of bottles today | bottles |
| Bottle Volume | Total bottle volume today | oz |
| Last Bottle | Time of last bottle | timestamp |
| Last Food | Time of last food | timestamp |
| Diaper Count | Total diapers today | diapers |
| Wet Diapers | Wet diaper count today | diapers |
| BM Diapers | BM diaper count today | diapers |
| Last Diaper | Time of last diaper change | timestamp |
| Activities | Number of activities today | activities |

### Binary Sensors

| Sensor | Description |
|--------|-------------|
| Sleeping | On when child is sleeping, off when awake |

### Calendar

The integration provides a DailyConnect Calendar entity that shows upcoming daycare events in the native Home Assistant calendar interface.

### Image Entities

| Entity | Description |
|--------|-------------|
| Latest Photo | Displays the most recent activity photo for each child |

**Note**: Photos are fetched from activities and cached. The image updates when new photos are posted to DailyConnect.

## Troubleshooting

### Authentication Issues

If you see authentication errors:
1. Verify your DailyConnect credentials are correct
2. Try logging into the DailyConnect website to confirm your account works
3. Check the Home Assistant logs for detailed error messages

### No Data

If sensors show "unknown" or "unavailable":
1. Ensure your child has activity logged for today
2. Check that the integration is connected (Settings > Devices & Services)
3. Try reloading the integration

## License

MIT License
