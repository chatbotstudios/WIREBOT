# Automation Rules Skill (rules.md)

To create or manage rules, use the `run_cli` tool.

## Creating Simple Rules
Use `run_cli("rule_create [key=value] ...")`
- One rule = one condition + one action type. Don't create two opposing rules - use on_action + off_action in a single rule.
- Conditions: `gt` (>), `lt` (<), `eq` (==), `neq` (!=), `change`, `always`
- Actions: `led_set`, `telegram`, `gpio_write`, `actuator`, `nats_publish`, `serial_send`

### LED Rules
`run_cli("rule_create sensor_name=chip_temp condition=gt threshold=45 on_action=led_set on_r=255 on_g=0 on_b=0")`

### Telegram Alerts
`run_cli("rule_create sensor_name=chip_temp condition=gt threshold=45 on_action=telegram on_telegram_message='Temp: {value}C'")`

## Managing Rules
- `run_cli("rule_list")` to list rules and get their IDs.
- `run_cli("rule_delete rule_id=[id]")` to delete a rule. Use `rule_id=all` to clear all.
