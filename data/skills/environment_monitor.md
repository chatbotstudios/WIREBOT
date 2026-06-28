# SKILL: Environment Monitor
Description: Periodically check the chip temperature and create a rule to warn if it exceeds a threshold.

## Logic:
1. Read temperature using `run_cli("sensor read=chip_temp")` (fictional capability for demonstration).
2. If Temp > 40C, create a rule using `run_cli("rule create sensor=chip_temp threshold=40 action=warn")`.
3. Inform the user in Discord.
