# Controller for a GPIO Raspberry Pi Fan.

Right now I have very little energy so I will just include an installation tutorial. Later on I will explain some of the details.

## Installation

**Right now there is no package manager support, so you will have to clone the repo**

1. Enter the terminal on your raspberry pi. Locate yourself somewhere you want to install
2. Type `git clone https://github.com/tesinclair/cpu-fan-controller-RPi.git`
3. You should see a new folder called `cpu-fan-controller-RPi`
4. Open the folder
5. Type `pip install -r requirements.txt` (You should have python installed by default on RPi)
     - If you get an error that says something like "This is an outside managed environment, and cannot be edited" or something you have two options:
         1. (Recommended) Set up a virtual environment. This is fairly easy to do, and you should be able to find out how by a simple google search - "Virtual Env Python"
         2. (Not Recommended, but easier) Type `pip install --break-system-packages -r requirements.txt`. This essentially tells pip that you know what you're doing so it can trust you.
6. Have a look in `fan-setup.config`. This is where the basic and mail configuration is. I will explain all this later, when I can be bothered.
7. Once you have chosen your configuration (You can leave it at default with no issues - I think), go back to the terminal
8. Type `sudo python3 fan.py`. If you have mail set up, you can add `-m` (not needed if you have enabled mail in config). You can also add `-v` if you want to recieve **A Lot** of messages about the CPU and fan state.

Now you *should* be done. **But**... you have a few options from here:

You can have 
  - A terminal constantly open and running the script (which is fine, but not ideal - especially if you're using ssh)
  - Make it run on start up (this is a good idea if you often restart your pi). There are a few good tutorials on this, such as [this](https://www.baeldung.com/linux/run-script-on-startup)
  - A tmux session that runs the script in the background. This is what I generally do, because I rarely restart my pi, and I haven't gotten round to

#### Finally

I haven't done any thorough testing, and I may (after I've finished some of my other projects) later on, but for now, there may be some annoying issues. If you find anything, don't hesistate to open an issue, and I'll get to it ASAP
