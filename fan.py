import RPi.GPIO as GPIO
import subprocess
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# -=-=-=-=-=- Global Definitions -=-=-=-=-=-=-

BOARD = GPIO.BCM

STATE_ON = True
STATE_OFF = False

FAN_ON = GPIO.HIGH
FAN_OFF = GPIO.LOW

FAN = 4 # Change this if your fan is not connected to GPIO 4

CHECK_DELAY = 30 # Change this if you want to check temp more or less frequently than 30 seconds

MAX_ATTEMPTS = 3 # Change this if you want to change the number of retries the program will attempt on error. Be reasonable as opening and closing channels too much can damage your pi.

# Threshold temperatures, feel free to change to your needs:
CRIT_HEAT = 90
WARN_HEAT = 70
FAN_START = 55


def setup() -> None:
    GPIO.setmode(BOARD) 
    GPIO.setup(FAN, GPIO.OUT)

def set_fan_state(state: int) -> int:
    GPIO.output(FAN, state)
    return state

def deinit() -> None:
    set_fan_state(FAN_OFF)
    GPIO.setup(FAN, GPIO.OUT)
    GPIO.cleanup()

def main() -> None:
    logging.basicConfig(filename="therm.log", level=logging.WARNING)

    fan_state = STATE_OFF
    
    while True:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000 # CPU temp is given in millidegrees

        if temp >= CRIT_HEAT:
            logger.critical(f"Core CPU temperature: {temp}, exceeded max temperature {CRIT_HEAT} by {temp - CRIT_HEAT} degrees on {datetime.now()}.\nShutting down system! Manual restart needed!")
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])

        elif temp >= WARN_HEAT:
            logger.warning(f"Core CPU temperature: {temp}, exceeded warning temperature {WARN_HEAT} by {temp - WARN_HEAT} degrees on {datetime.now()}.\nAvoid Strenuous CPU Usage!")
            if fan_state != STATE_ON:
                fan_state = set_fan_state(FAN_ON)
            
        elif temp >= FAN_START:
            if fan_state != STATE_ON:
                fan_state = set_fan_state(FAN_ON)

        elif temp < FAN_START:
            if fan_state != STATE_OFF:
                fan_state = set_fan_state(FAN_OFF)

        else:
            logger.error(f"Unaccounted for temperature: {temp}. Please log an issue here: https://github.com/tesinclair/rpi-temp-controller")

        time.sleep(CHECK_DELAY)

            

if __name__ == '__main__':
    attempts = 0

    while attempts < MAX_ATTEMPTS:
        try:
            setup()
            main()
        except Exception as e:
            print(f"[ERROR]: Control system failed attempt: {attempts + 1} for the following reason(s): {e}. Will retry is attempts does not exceed 3.")
            logger.error(e)
            attempts += 1

        except KeyboardInterrupt:
            print("Program forcefully closed. Not logging or restarting.")
            attempts = 100

        finally:
            deinit()

