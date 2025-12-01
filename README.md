# Controller for a GPIO Raspberry Pi Fan.

## Installation

**Right now there is no package manager support, so you will have to clone the repo**

1. Enter the terminal on your raspberry pi. Locate yourself somewhere you want to install
2. Type `git clone --depth=1 https://github.com/tesinclair/cpu-fan-controller-RPi.git`
3. You should see a new folder called `cpu-fan-controller-RPi`
4. Open the folder
5. Type `pip install -r requirements.txt` (You should have python installed by default on RPi)
     - If you get an error that says something like "This is an outside managed environment, and cannot be edited" or something you have two options:
         1. (Recommended) Set up a virtual environment. This is fairly easy to do, and you should be able to find out how by a simple google search - "Virtual Env Python"
         2. (Not Recommended, but easier) Type `pip install --break-system-packages -r requirements.txt`. This essentially tells pip that you know what you're doing so it can trust you.
6. Have a look in `fan-setup.config`. This is where the basic and mail configuration is. I will explain all this later, when I can be bothered.
7. Once you have chosen your configuration (You can leave it at default with no issues - I think), go back to the terminal
8. Type `sudo python3 fan.py &`. If you have mail set up, you can add `-m` (not needed if you have enabled mail in config). You can also add `-v` if you want to recieve **A Lot** of messages about the CPU and fan state.
