import RPi.GPIO as GPIO
import subprocess
import time
from datetime import datetime
import logging
import configparser
import smtplib
from email.mime.text import MIMEText
import argparse
import ast


logger = logging.getLogger(__name__)


# =-=-=-=-=- DO NOT EDIT -=-=-=-=-=-=-=-
STATE_ON = True
STATE_OFF = False

FAN_ON = GPIO.HIGH
FAN_OFF = GPIO.LOW

config = configparser.ConfigParser(inline_comment_prefixes="#")
config.read('fan-setup.config')

BOARD = getattr(GPIO, config['BASIC']['board'])
FAN = int(config['BASIC']['fan'])
CHECK_DELAY = int(config['BASIC']['check_delay'])
MAX_ATTEMPTS = int(config['BASIC']['max_attempts'])
LOGGING_LEVEL = getattr(logging, config['BASIC']['logging_level'])
VERBOSITY = ast.literal_eval(config['BASIC']['verbosity'])
CRIT_HEAT = int(config['BASIC']['crit_heat'])
WARN_HEAT = int(config['BASIC']['warn_heat'])
FAN_START = int(config['BASIC']['fan_start'])

EMAIL_LOGGING = bool(config['SMTP']['email_logging'])
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

    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        try:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, SMTP_TO, msg.as_string())

        except smtplib.SMTPAuthenticationError as e:
            log_msg = f"Authentication failed. This is likely because either the email or password was incorrect. Make sure to update the examples if you haven't already, or double check your data. For those who are technically inclined, here is the error: {e}"
            print(log_msg)
            logger.error(log_msg)

        except smtplib.SMTPConnectError as e:
            log_msg = f"The connection to the smtp server you are using failed. This could be because the server is down, your internet isn't working, or the server doesn't like you. Here is the error it may shed some light on the issue: {e}"
            print(log_msg)
            logger.error(log_msg)

        except smtplib.SMTPException as e:
            log_msg = f"This could be anything. It is likely a case that I was too lazy to code for. If the error looks to be on my end, you can raise an issue here: https:www.github.com/tesinclair/cpu-fan-controller-RPi. Here is the error: {e}"
            print(log_msg)
            logger.error(log_msg)

def main() -> None:
    logging.basicConfig(filename="therm.log", level=LOGGING_LEVEL)

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

            if VERBOSITY:
                print(log_msg)

            if fan_state != STATE_ON:
                fan_state = set_fan_state(FAN_ON)
            
        elif temp >= FAN_START:
            log_msg = f"Core CPU temperature: {temp} has exceeded the fan start threshold {FAN_START} by {temp - FAN_START} degrees on {datetime.now()}.\n If you would not like to recieve info messages you can turn verbosity off in fan_setup.config"
            logger.info(log_msg)

            if VERBOSITY:
                print(log_msg)

                if EMAIL_LOGGING:
                    log_email("[INFO]: Fan On", log_msg)

            if fan_state != STATE_ON:
                fan_state = set_fan_state(FAN_ON)

        elif temp < FAN_START:
            log_msg = f"Core CPU temperature: {temp} is now below the fan start threshold {FAN_START} on {datetime.now()}.\nIf you would not like to recieve info messages you can turn verbosity off in fan_setup.config"
            logger.info(log_msg)

            if VERBOSITY:
                print(log_msg)

                if EMAIL_LOGGING:
                    log_email("[INFO]: Fan Off", log_msg)

            if fan_state != STATE_OFF:
                fan_state = set_fan_state(FAN_OFF)

        else:
            log_msg = f"Unaccounted for temperature: {temp}. Please log an issue here: https://github.com/tesinclair/rpi-temp-controller"
            logger.error(log_msg)

            if EMAIL_LOGGING:
                log_email("CASE ERROR:", log_msg)

            if VERBOSITY:
                print(log_msg)

        time.sleep(CHECK_DELAY)

            

if __name__ == '__main__':
    attempts = 0

    parser = argparse.ArgumentParser(prog="CPU Fan Controller for RPi", description="Safely controls a GPIO fan for CPU health. Shuts down pi if a maximum head is reached, and logs important system changes", epilog="")

    parser.add_argument("-m", "--mail", action="store_true", help="Recieve mail updates on pi logs")
    parser.add_argument("-v", "--verbose", action="store_true", help="Recieve messages and logs on all events")
    args = parser.parse_args()

    if args.mail:
        EMAIL_LOGGING = True

    if args.verbose:
        LOGGING_LEVEL = logging.INFO
        VERBOSITY = True

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
            log_msg = "Program forcefully closed. Not logging or restarting."
            print(log_msg)

            log_msg += f"Raised on {datetime.now()}"
            logger.info(log_msg)
                
            if EMAIL_LOGGING:
                log_email("[INFO] Program Force Closed", log_msg)

            attempts = MAX_ATTEMPTS + 100

        finally:
            deinit()

