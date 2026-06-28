# Hardware & Devices Skill (devices.md)

To manage external hardware, use `run_cli`.

## Device Registry
- "chip_temp" is pre-registered.
- "clock_hour", "clock_minute", "clock_hhmm" are pre-registered for time-based triggers.

## Registering Actuators
`run_cli("device_register name=[name] type=[type] pin=[pin]")`
- Types: `digital_out`, `relay` (inverted), `pwm`.
- Example: `run_cli("device_register name=fan type=relay pin=5")`

## Registering NATS Virtual Sensors
`run_cli("device_register name=[name] type=nats_value subject=[topic]")`
- Stores last value from NATS. JSON supported (`{"value": 1.2, "message": "..."}`).

## Registering Serial UART
`run_cli("device_register name=[name] type=serial_text baud=9600")`
- Only one allowed. Uses RX19/TX20 on S3.
