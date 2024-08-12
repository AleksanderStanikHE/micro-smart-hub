# Micro Smart Hub

Micro Smart Hub is a flexible and lightweight smart home automation platform designed for managing various devices and automations. It is easy to extend and configure, making it ideal for a wide range of home automation tasks.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Running the Scheduler Application](#running-the-scheduler-application)
4. [Developing with Micro Smart Hub](#developing-with-micro-smart-hub)
5. [Extending with New Automations](#extending-with-new-automations)
6. [Creating New Devices](#creating-new-devices)
7. [Configuration](#configuration)
8. [Examples](#examples)
9. [License](#license)

## Features

- Supports custom automations and devices
- Asynchronous scheduling of tasks
- Configuration via YAML files
- Lightweight and portable

## Installation

Micro Smart Hub is available as a Python package and can be installed using pip:

```bash
pip install microsmarthub
```

## Running the Scheduler Application

To run the Micro Smart Hub scheduler, use the `micro-smart-server` command-line application. This application reads configuration files and manages the execution of scheduled tasks.

### Usage

```bash
micro-smart-server [options]
```

### Options

- `-s`, `--schedule`: Path to the schedule YAML file. Default is `./schedule.yaml`.
- `-d`, `--devices`: Directories containing device modules. Default is the current directory.
- `-a`, `--automations`: Directories containing automation modules. Default is the current directory.
- `-c`, `--config`: Path to the configuration YAML file. Default is `./config.yaml`.

### Example

'''bash
micro-smart-server -s ./schedule.yaml -d ./devices ./extra_devices -a ./automations ./extra_automations -c ./config.yaml
'''

## Developing with Micro Smart Hub

### Extending with New Automations

To create a new automation, inherit from the `Automation` class and implement the `run` method:

```python
from micro_smart_hub.registry import register_class
from micro_smart_hub.automation import Automation


@register_class
class MyAutomation(Automation):
    def run(self, action, parameters, devices):
        print(f"Running {action} with parameters {parameters} on devices {devices}")
```

### Creating New Devices

To create a new device, inherit from the `MicroDevice` class and implement the required methods:

```python
from micro_smart_hub.registry import register_class
from micro_smart_hub.device import MicroDevice
import requests


@register_class
class MyIoTSwitch(IoTSwitch):
    def __init__(self, definition=None):
        super().__init__(definition)
        self.device_id = self.definition.get("device_id", "default_id")

    def load_info(self):
        response = requests.get(f"http://{self.device_id}/info")
        self.info = response.json().get('device', {})

    def load_state(self):
        response = requests.get(f"http://{self.device_id}/state")
        self.status = response.json().get('status', {})

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        if value:
            requests.post(f"http://{self.device_id}/turn_on")
        else:
            requests.post(f"http://{self.device_id}/turn_off")
        self._on = value

    def off(self):
        self.on = False
```

## Configuration

Configuration is done via YAML files. Define your schedule, devices, and automations in separate YAML files.

### Schedule Example

```yaml
FakeAutomation:
  schedule:
    monday:
      - time: 6       # Without minutes (6:00)
        action: on
      - time: 18.30   # With minutes
        action: off
  devices:
    - FakeSwitch

Irrigation:
  schedule:
    monday:
      - time: "6:05"    # With minutes but as a string
        action: on
      - time: 18      # Without minutes (18:00)
        action: off
  devices:
    - Irrigation_Pump
```

### Device Configuration Example (config.yaml)

Define your devices and their parameters in a config.yaml file. Here is an example configuration:
```yaml
Pump:
  class: SwitchBox
  parameters:
    url: 192.168.0.3

Garden Light:
  class: SwitchBox
  parameters:
    url: 192.168.0.197      

SmartIrrigation:
  class: Irrigation
  parameters:
    latitude: 12.24541322
    longitude: 32.32243421

# Pump: An instance of SwitchBox with a specific IP address.
# Garden Light: Another SwitchBox with a different IP.
# SmartIrrigation: An instance of Irrigation with specific geolocation parameters.
```

## Examples

Check out the `examples` directory for more detailed examples of how to set up and run automations and devices.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all contributors and users for their support and feedback.