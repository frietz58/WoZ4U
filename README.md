# Usage
    TODO steps: Clone, make venv, install naoqi api
1. Clone the Repo: `git clone https://github.com/frietz58/wizard_of_oz_pepper.git`
1. Install virtualenv: `sudo pip install virtualenv`
2. Make python2.7 virtualenv: `virtualenv --python=/usr/bin/python2.7 venv`
3. Install requirements: `cd wizard_of_oz_pepper && pip install -r requirements.txt`
4. Set the path to point to your local installation of NaoQi API in `set_paths.sh`
5. Source the script: `chmode +x set_paths.sh && source set_paths.sh`
6. Run the server:`python server.py`