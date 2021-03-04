# Table of Contents

+ [Download the required frameworks](#download-the-required-frameworks)
+ [Download WoZ4U](#dpwnload-woz4u)
+ [Setting up the environment](#setting-up-the-environment)
  + [Pass NAOqi-API reference](#pass-naoqi-api-reference)
  + [Create virtual environment](#create-virtual-environment)
  + [Install requirements](#install-requirements)
+ [Running WoZ4U](#running-woz4u)

# WoZ4U Guide for Windows

In this guide we provide the steps and commands to install and run WoZ4U on Windows machines. These are slightly different from the process to install and run WoZ4U on MacOs or Linux, because:

+ Bash is not available per default
+ Python's virtual environment works slightly different
+ Environment variables are handled completely different

Thus, we found a dedicated guide to install WoZ4U on Windows beneficial, of not necessary.



### Download the required frameworks

To begin, you will have to download and install a few additional software components:

1. **Install Git for Windows** from [here](https://git-scm.com/download/win). The setup if quite long, but you should be fine to just leave all options on the default values. Alternatively, [here](https://www.stanleyulili.com/git/how-to-install-git-bash-on-windows/) is a guide explaining the individual steps in greater detail. After you have completed this setup, **Git Bash** is available on your system, you should be able to launch it the start menu. You will need this to a) clone WoZ4U from GitHub, but also to type the commands to install the requirements and ultimately to start the main interface.
2. **Install Python 2.7** from [here](https://www.python.org/downloads/release/python-2716/). Independent of your system architecture, you have to **install the 32 bit version**. This is, because the NAOqi-API has only been compiled for 32 bit systems. Thus, if you install the 64 bit version Python 2.7 the NAOqi-API will throw errors and prevent you from using WoZ4U. Luckily, Windows 10 handles this well, and you can just install the 32 bit version of Python, even if you are on a 64 bit machine.
3. **Install PyCharm** from [here](https://www.jetbrains.com/help/pycharm/installation-guide.html). This step is somewhat optional, however, we found that using Pycharm to setup a virtual environment is, by far, the most convenient and easiest way to do it. You can either install the free community edition, request and EDU license or, if you have one, use your professional license.
4. **Download the NAOqi-SDK** from [here](https://developer.softbankrobotics.com/pepper-2-5/downloads/pepper-naoqi-25-downloads-windows). Notice, how the SDK is only available in 32 bit. This is why you had to install the 32 bit version of Python 2.7 earlier. Extract the zip to any location, remember this location, you have to specify it in the next step.



### Download WoZ4U

Download WoZ4U from GitHub using GitBash, that you installed earlier:

1. Start the GitBash by searching for it in the start menu. This will spawn a Bash terminal, looking similar to this:
   <img src="readme_imgs/gitbash.png">
2. Using the `cd` command in GitBash, navigate to the location where you would like to install WoZ4U, for example on the Desktop: `cd Desktop`
3. Download (clone) the WoZ4U repository onto your machine: `git clone https://github.com/frietz58/WoZ4U.git`. **Don't paste this command** (or anything for that matter) into your GitBash terminal using `CTRL + V`! Instead right-click into the terminal and select paste or type the command manually. If you press `CTRL + V` in GitBash, you will get [this error](https://stackoverflow.com/questions/53988638/git-fatal-protocol-https-is-not-supported).

You should now have a folder called `WoZ4U` at the location where you executed the git clone command. You can verify this by inspecting the location with the Windows Explorer.



### Setting up the environment

This is the trickiest part of the installation, because it is very easy to mess anything up, given how Windows handles environment variables. Thus, we use PyCharm to do the heavy lifting and set up the environment. If you feel confident enough and know what you are doing, you can of course create the virtual environment, otherwise, just follow the steps below:

#### Pass NAOqi-API reference

In order for Python to know where the NAOqi-API is available, you need to add the location of the of the folder to the `PYTHONPATH`. This environment variable contains all the "locations" the Python interpreter will search for packages. Edit the script called `set_paths.sh` in the WoZ4U folder, for example by right-clicking it and opening it Notepad. If you double-click the file, Windows will treat it as an executable (because it is one)  and run the file, but won't let you edit it.

In the code of the file, identify the first occurrence of the string "PYTHONPATH" (line 4). Adjust value of the the in the in quotes so that it contains the path to the lib folder inside the NAOqi-SDK folder, that you downloaded and extracted earlier:

``` bash
# PYTHONPATH="C:\ABSOLUTE\PATH\TO\LIB\FOLDER\IN\NAOQI-API-FOLDER";
PYTHONPATH="C:\Users\Finn\Desktop\WoZ4U\pynaoqi-python2.7-2.5.7.1-win32-vs2013\lib";
```



#### Create virtual environment

1. Start PyCharm.

2. Open the WoZ4U folder in Pycharm (`File` --> `Open`). PyCharm might work for a short moment because it scans all the files in the selected directory, but after that, you should see the files in the WoZ4U folder displayed on the right hand site of PyCharm.

3. Open the "Project settings" of the WoZ4U project: `File` --> `Settings`. Alternatively, press `CTRL + ALT + S`.

4. In the project settings, navigate to the `Python Interpreter` settings (marked with 1) in the following screenshot). Under the interpreter settings,  open the dropdown menu and press the `Show all... option` (marked with 2) in the screenshot):

   <img src="readme_imgs/pycharm_settings.png"> 

5. In the list of all available python interpreters (if you never used Python before, there should only be one interpreter called Python 2.7), select the plus button to add a new one (1) in the screenshot. The, create a `New environment` (2) in the screenshot). Leave the location as default, which will create the virtual environment inside the project folder This is important, because we assume this location of the environment later. Make sure that you select your Python 2.7 installation as base interpreter (3) in the screenshot). Again, if you just installed Python, there should only be one option. Name the virtual environment as you like (default is `venv`), but you can also call it `woz4u_venv` if you prefer a more descriptive name.
   <img src="readme_imgs/pycharm_venv.png">

6. Press `OK`. Pycharm will now create your virtual environment. After the process has finished, press `OK`in the remaining dialogues. 

To verify that the virtual environment was created, either in with the Windows Explore or with the file view in Pycharm, check that at the location specified in the setup, a new folder as been created with the following structure:

<img src="readme_imgs/venv_structure.png">

Notice that there is a script called `activate` in the `venv/Scripts/` folder. We will call this later to activate the virtual environment.



#### Install requirements

Now that we have a virtual environment, the last step is to install the python requirements for WoZ4U. 

For this, activate the the virtual environment we just created. This is done by "sourcing" the activate script inside the virtual environment's `Script` folder:

1. In GitBash, navigate to the folder where the virtual environment is located. If you followed the guide without deviation, it will be located inside the WoZ4U folder: `cd path/to/WoZ4U-folder/`
2. Activate the virtual environment `source venv/Scripts/activate`

This should output, in paranthesis, the name of the virtual environment you just activated. If you left the default value in the PyCharm dialogue, it will output `(venv)`.  Further, GitBash will display the name of the active environment after every command you execute, while that environment is active. See the annotations in the following screenshot:

<img src="readme_imgs/active_venv.png">

3. Install the requirements *inside* of the currently active environment (because we just activate the virtual environment for WoZ4U, there won't be any conflicting package versions): `pip install -r requirements.txt`

That's it. You are now able to start the interface and connect it to a Pepper robot.



### Running WoZ4U

The main command to start the WoZ4U interface is to tell Python to execute the file `server.py`. However, two other requirements must be met. The required packages (that have been installed in the virtual environment) must be available, as well as the NAOqi-API, so that Python can send commands to Pepper. 

If you just completed the installation guide, your GitBash terminal should still have the virtual environment active. Nevertheless, we provide a command that executes all the steps, so that it will also work after restarting your computer or after opening a new GitBash terminal.

1. Make sure the GitBash terminal's working directory is set to the WoZ4U folder (`cd /Path\to\WoZ4U`)

2. Start the server by running: ` source venv/Scripts/activate && source set_paths.sh && python server.py`
   You can see the three separate commands, combined via the `&&` operator. First ` source venv/Scripts/activate` activates the virtual environment. Then `source set_paths.sh` executes the script `set_paths.sh `so that Python knows where to find the NAOqi-API. Finally, `python server.py` starts the main interface.

   The output of that command should be similar to this:

   <img src="readme_imgs/woz4u_running.png">

3. To access the interface, start any browser (we recommend FireFox), and type into the URL field: `http://localhost:5000/`

   You can now use WoZ4U in your browser: 

<img src="readme_imgs/woz4u_windows.png">



Head back to the main README to learn how you can configure the UI elements of the interface and how to establish a connection between the interface in the browser and your Pepper robot.