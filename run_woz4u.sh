abs_naoqi_path=/Users/finn/Desktop/WTM/pepper_scripts/pynaoqi-python2.7-2.5.7.1-mac64/lib/python2.7/site-packages
abs_naoqi_lib_path=/Users/finn/Desktop/WTM/pepper_scripts/pynaoqi-python2.7-2.5.7.1-mac64/lib
abs_venv_activate_path=/Users/finn/Desktop/Umea_project/venv/bin/activate

export PYTHONPATH=${PYTHONPATH}:$abs_naoqi_path
export DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH}:$abs_naoqi_lib_path
source $abs_venv_activate_path

python server.py