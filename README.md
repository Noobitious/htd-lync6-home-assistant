# HTD Lync6 Home Assistant Integration

This custom integration allows you to control the HTD Lync6 audio distribution system directly from Home Assistant. It supports advanced features such as scene presets, volume ramping, zone grouping, and energy-saving mode, providing a seamless and enhanced audio experience. It's a fair amount different from the parent it forked from thanks significant ChatGPT tinkering.

## Features

### Core Features

1. **Power Control**: Turn zones on or off.
2. **Volume Control**: Adjust the volume of individual zones.
3. **Source Selection**: Choose audio sources for each zone.

### Advanced Features

1. **Scene Presets**:
   - Save and recall custom configurations for zones, including power state, volume, mute state, and source selection.
   - **Use Case**: Quickly switch to common setups, like "Movie Night" or "Party Mode."
     ```yaml
     # Save the current state of a zone as a preset
     service: media_player.htd_save_preset
     data:
       entity_id: media_player.master
       name: MovieNight

     # Recall a previously saved preset
     service: media_player.htd_recall_preset
     data:
       entity_id: media_player.master
       name: MovieNight
     ```

2. **Volume Ramping**:
   - Gradually adjust the volume to a target level over a specified duration.
   - **Use Case**: Smoothly increase or decrease volume to avoid sudden changes.
     ```yaml
     service: media_player.htd_ramp_volume
     data:
       entity_id: media_player.living
       target_volume: 75  # Target volume level (0-100)
       duration: 15        # Time in seconds to reach the target volume
     ```

3. **Zone Grouping**:
   - Group zones for synchronized control of volume and source.
   - **Use Case**: Manage multiple zones together for events like parties.
     ```yaml
     # Create a group of zones
     service: media_player.htd_create_group
     data:
       group_name: GroundLevelParty
       zones:
         - media_player.garage
         - media_player.living
         - media_player.patio

     # Set the volume for all zones in a group
     service: media_player.htd_set_group_volume
     data:
       group_name: PartyMode
       volume: 50  # Volume level (0-100)
     ```

4. **Energy-Saving Mode**:
   - Automatically turn off zones after a specified period of inactivity.
   - **Use Case**: Save energy by turning off outdoor speakers left on after a BBQ.
     ```yaml
     service: media_player.htd_energy_saving
     data:
       entity_id: media_player.patio
       timeout: 1200  # Timeout in seconds (e.g., 20 minutes)
     ```

## Installation

### 1. Manual Installation

1. Download this repository as a ZIP file and extract it.
2. Copy the `htd_lync6` folder to your Home Assistant `custom_components` directory (could be in a different root folder, such as homeassistant/custom_components/htd_lync6/ or like this example:
   ```
   /config/custom_components/htd_lync6/
   ```

### 2. YAML Configuration

Add the following to your `configuration.yaml`:
```yaml
htd_lync6:
  host: 192.168.2.63  # Replace with the IP address of your HTD controller
  zones:
    - Master
    - Ensuite
    - Living
    - Basement
    - Patio
    - Garage
  sources:
    - NA 1
    - NA 2
    - Living Room TV
    - Basement TV
    - NA 5
    - NA 6
    - NA 7
    - MusicCast
    - NA 9
    - NA 10
    - NA 11
    - NA 12
```

### 3. Restart Home Assistant

Restart Home Assistant again to apply the configuration.

## Troubleshooting

1. **Entities Not Appearing**:
   - Ensure your `configuration.yaml` is valid using the "Check Configuration" tool in Home Assistant.
   - Check the logs for errors related to `htd_lync6`.

2. **Communication Issues**:
   - Verify that the IP address for your HTD controller is correct and reachable from Home Assistant.
   - Ensure your network allows traffic on the controller's port (default: 10006).

3. **Debug Logging**:
   - Enable debug logging to capture more details:
     ```yaml
     logger:
       default: warning
       logs:
         custom_components.htd_lync6: debug
     ```

## Acknowledgments

This integration is a fork of several previous works including
* https://github.com/UngluedChalice/htd-lync12-home-assistant)
* https://github.com/hikirsch/htd_mc-home-assistant
* https://github.com/whitingj/mca66
* https://github.com/steve28/mca66
* http://www.brandonclaps.com/?p=173

UngluedChalice credits [sashman](https://github.com/sashman/), whose early work on RS-232 control for the HTD system laid the groundwork for many of the integration features. I am uploading the RS232 codes for reference only (if HTD objects I will remove).
