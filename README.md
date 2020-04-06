# HTD MC Series integration for Home Assistant

This integration will add the HTD MCA66 into Home Assistant.

## Installation steps

1. Download the 4 files (`__init__.py`, `htd_mc.py`, `media_player.py`, `manifest.json`) from this repo and place them into your `custom_components/htd_mc` folder.
2. Update your configuration.yaml to include the following (NOTE: Only host is required)
    ```yaml
    htd_mc:
      host: 192.168.1.123
      port: 10006
      zones:
        - Kitchen
        - Dining Room
        - Living Room
      sources:
        - Chrome Cast
        - FM/AM
    ```
3. Restart Home Assistant

## Code Credits
- https://github.com/whitingj/mca66
- https://github.com/steve28/mca66
- http://www.brandonclaps.com/?p=173