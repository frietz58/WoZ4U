# WoZ4U Guide for Windows

In this guide we provide the steps and commands to install and run WoZ4U on Windows machines. These are slightly different from the process to install and run WoZ4U on MacOs or Linux, because:

+ Bash is not available per default
+ Python's virtual environment works slightly different
+ Environment variables are handled completely different

Thus, we found a dedicated guide to install WoZ4U on Windows beneficial, of not necessary.



### Download the required framework

To begin, you will have to download and install a few additional software components:

1. **Install Git for Windows** from [here](https://git-scm.com/download/win). The setup if quite long, but you should be fine to just leave all options on the default values. Alternatively, [here](https://www.stanleyulili.com/git/how-to-install-git-bash-on-windows/) is a guide explaining the individual steps in greater detail. After you have completed this setup, **Git Bash** is available on your system, you should be able to launch it the start menu. You will need this to a) clone WoZ4U from GitHub, but also to type the commands to install the requirements and ultimately to start the main interface.
2. **Install Python 2.7** from [here](https://www.python.org/downloads/release/python-2716/). Independent of your system architecture, you have to **install the 32 bit version**. This is, because the NAOqi-API has only been compiled for 32 bit systems. Thus, if you install the 64 bit version Python 2.7 the NAOqi-API will throw errors and prevent you from using WoZ4U. Luckily, Windows 10 handles this well, and you can just install the 32 bit version of Python, even if you are on a 64 bit machine.
3. **Install PyCharm** from [here](https://www.jetbrains.com/help/pycharm/installation-guide.html). This step is somewhat optional, however, we found that using Pycharm to setup a virtual environment is, by far, the most convenient and easiest way to do it. You can either install the free community edition, request and EDU license or, if you have one, use your professional license.
4. **Download the NAOqi-SDK** from [here](https://developer.softbankrobotics.com/pepper-2-5/downloads/pepper-naoqi-25-downloads-windows). Notice, how the SDK is only available in 32 bit. This is why you had to install the 32 bit version of Python 2.7 earlier. Extract the zip to any location, remember this location, we have to specify it later again.



### Download WoZ4U

Download WoZ4U from GitHub using GitBash, that you installed earlier:

1. Start the GitBash by searching for it in the start menu. This will spawn a Bash terminal, looking similar to this:
   TODO
2. Using the `cd` command in GitBash, navigate to the location where you would like to install WoZ4U, for example on the Desktop: `cd TODO`
3. Download (clone) the WoZ4U repository onto your machine: `git clone https://github.com/frietz58/WoZ4U.git`. **Don't paste this command** (or anything for that matter) into your GitBash terminal using `CTRL + V`! Instead right-click into the terminal and select paste or type the command manually. If you press `CTRL + V` in GitBash, you will get [this error](https://stackoverflow.com/questions/53988638/git-fatal-protocol-https-is-not-supported).

You should now have a folder called `WoZ4U` at the location where you executed the git clone command. You can verify this by inspecting the location with the Windows Explorer.



### Setting up the environment

This is the trickiest part of the installation, because it is very easy to mess anything up, given how Windows handles environment variables. Thus, we use PyCharm to do the heavy lifting and set up the environment. If you feel confident enough and know what you are doing, you can of course create the virtual environment, otherwise, just follow the steps below:

1. Start PyCharm.

2. Open 

   
   

1. Make venv with Pycharm
4. activate repo with gitbash: source ./venv/Scripts/activate
5. install requirements: pip install -r requirements.txt
6. adjust path in set_path for windows: PYTHONPATH="C:\Users\Finn\Desktop\WoZ4U\pynaoqi-python2.7-2.5.7.1-win32-vs2013\lib";
7. Run server: source venv/Scripts/activate && source set_paths.sh && python server.py
8. Access by typing "localhost:5000" in URL


