# MicroSmartHub

MySmartHome is a smart home automation system that includes a weekly scheduler. The first implementation focuses on `IrrigationAutomation`, which leverages weather forecasts to control an irrigation system. This system includes a simple irrigation controller and a pump switch (`SmartSwitch`) inherited from `MicroDevice`.

## Features

- **Weather Forecast Integration**: Uses weather forecasts to check soil moisture and wind levels.
- **Irrigation Automation**: Automatically controls irrigation based on weather conditions.
- **Smart Device Control**: Controls a pump switch (`SmartSwitch`) to manage irrigation.
- **Weekly Scheduler**: Schedules irrigation activities throughout the week.

## System Architecture

The MySmartHome system includes the following components:

- **MicroDevice**: Base class for all IoT devices.
- **SmartSwitch**: Inherits from `MicroDevice` and controls the irrigation pump.
- **IrrigationAutomation**: Manages the irrigation system based on weather forecasts and controls the `SmartSwitch`.
- **Weather Forecast API**: Provides soil moisture and wind level data for decision making.
- **Weekly Scheduler**: Schedules and automates tasks on a weekly basis.

## Diagram

```mermaid
graph TD
    subgraph MicroSmartHub
        F[Weekly Scheduler] --> D[IrrigationAutomation]
        A[MicroDevice] --> B[SmartSwitch]
        B --> C[Pump Control]
        D --> B
        D <--> E[Weather Forecast API]
    end