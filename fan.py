import RPi.GPIO as GPIO
import subprocess
import time
from datetime import datetime
import logging
import configparser
import smtplib
from email.mime.text import MIMEText
import argparse


logger = logging.getLogger(__name__)


# =-=-=-=-=- DO NOT EDIT -=-=-=-=-=-=-=-
STATE_ON = True
STATE_OFF = False

FAN_ON = GPIO.HIGH
FAN_OFF = GPIO.LOW

config = configparser.ConfigParser()
config.read('fan-setup.config')

BOARD = getattr(GPIO, config['BASIC']['BOARD'])
FAN = int(config['BASIC']['FAN'])
CHECK_DELAY = int(config['BASIC']['CHECK_DELAY'])
MAX_ATTEMPTS = int(config['BASIC']['MAX_ATTEMPTS'])
CRIT_HEAT = int(config['BASIC']['CRIT_HEAT'])
WARN_HEAT = int(config['BASIC']['WARN_HEAT'])
FAN_START = int(config['BASIC']['FAN_START'])

EMAIL_LOGGING = config['SMPT']['email_logging'])
SMTP_SERVER = config['SMTP']['server']
SMTP_PORT = int(config['SMTP']['port'])
SMTP_USER = config['SMTP']['user']
SMTP_PASSWORD = config['SMTP']['password']
SMTP_FROM = config['SMTP']['from']
SMTP_TO = config['SMTP']['to']

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

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

def log_email(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = SMTP_TO

    with smptlib.SMTP(SMTP_SEVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, SMTP_TO, msg.as_string())

def main() -> None:
    logging.basicConfig(filename="therm.log", level=logging.WARNING)
    if EMAIL_LOGGINGL
    send_email("Fan Off", f"Fan has been switched off for temp:")

    fan_state = STATE_OFF
    
    while True:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000 # CPU temp is given in millidegrees

        if temp >= CRIT_HEAT:
            log_msg = f"Core CPU temperature: {temp}, exceeded max temperature {CRIT_HEAT} by {temp - CRIT_HEAT} degrees on {datetime.now()}.\nShutting down system! Manual restart needed!"
            logger.critical(log_msg)

            if EMAIL_LOGGING:
                log_email("CRITICAL CPU TEMPERATURE", log_msg)

            subprocess.run(['sudo', 'shutdown', '-h', 'now'])

        elif temp >= WARN_HEAT:
            log_msg = f"Core CPU temperature: {temp}, exceeded warning temperature {WARN_HEAT} by {temp - WARN_HEAT} degrees on {datetime.now()}.\nAvoid Strenuous CPU Usage!"
            logger.warning(log_msg)

            if EMAIL_LOGGING:
                log_email("WARNING CPU TEMPERATURE", log_msg)

            if fan_state != STATE_ON:
                fan_state = set_fan_state(FAN_ON)
            
        elif temp >= FAN_START:
            if fan_state != STATE_ON:
                fan_state = set_fan_state(FAN_ON)

        elif temp < FAN_START:
            if fan_state != STATE_OFF:
                fan_state = set_fan_state(FAN_OFF)

        else:
            log_msg = f"Unaccounted for temperature: {temp}. Please log an issue here: https://github.com/tesinclair/rpi-temp-controller"
            logger.error(log_msg)
            if EMAIL_LOGGING:
                log_email("CASE ERROR:", log_msg)

        time.sleep(CHECK_DELAY)

            

if __name__ == '__main__':
    attempts = 0

    parser = argparse.ArgumentParser(prog="CPU Fan Controller for RPi", description="Safely controls a GPIO fan for CPU health. Shuts down pi if a maximum head is reached, and logs important system changes", epilog="")

    parser.add_argument("-m", "--mail", action="store_true")
    args = parser.parse_args()

    if args.mail:
        EMAIL_LOGGING = True

    while attempts < MAX_ATTEMPTS:
        try:
            setup()
            main()
        except Exception as e:
            print(f"[ERROR]: Control system failed attempt: {attempts + 1} for the following reason(s): {e}. Will retry if attempts does not exceed {MAX_ATTEMPTS}.")
            logger.error(e)

            if EMAIL_LOGGING:
                log_email("[ERROR]: Control System Failed", e)

            attempts += 1

        except KeyboardInterrupt:
            print("Program forcefully closed. Not logging or restarting.")
            attempts = MAX_ATTEMPTS + 100

        finally:
            deinit()

