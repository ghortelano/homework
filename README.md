# homework
Simple script to validate Tachometer signal vs PWM setting

This script launches tachometer_logger concurrently, while processing input for pwm_input. 
pwm_input = 1 to 100 is a PASS condition.
pwm_input > 100 is a FAIL condition.

A logfile will be generated upon exiting the script.

Initial conditions:
pwm_input = 0
LOG_INTERVAL = 3 seconds
MAX_TACHO = 3000

Upon executing the script: Type a number ANYTIME into the ongoing LOG to set PWM (can be >100). Type 'q' or 'quit' to exit.

