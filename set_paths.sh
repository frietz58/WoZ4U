if [[ "$OSTYPE" == "msys" ]]; then
  # set env variables on windows, assuming GitBash shell
  echo Setting environment variables for GitBash on Windows:
  #set your path here
  PYTHONPATH="C:\Users\deepa\anaconda3\envs\sce_env\Lib\site-packages\naoqi\lib";
  export PYTHONPATH
  echo $PYTHONPATH
else
  # set env variables on linux/mac
  echo Setting environment variables for Bash on Linux/Mac
  #set your path here
  export PYTHONPATH=${PYTHONPATH}:/Users/finn/Desktop/WTM/pepper_scripts/pynaoqi-python2.7-2.5.7.1-mac64/lib/python2.7/site-packages
  export DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH}:/Users/finn/Desktop/WTM/pepper_scripts/pynaoqi-python2.7-2.5.7.1-mac64/lib
fi