# os=$(uname -a | awk '{print $1;}')
# 
# if [ "$os"  = "Linux" ]; then
# 	echo "On Linux"
# elif ["$os" = "Darwin" ]; then
# 	echo "On Mac"
# else
# 	echo "Else"
# fi

  echo
  echo "Determining active operating system via \$OSTYPE"
  echo " » \$OSTYPE output: $OSTYPE"

  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    active_os="Linux"
    echo " ✔ Active Operating System: ${active_os}"
    
    sudo docker run -it --network host --device /dev/snd frietz58/woz4u	

  elif [[ "$OSTYPE" == "darwin"* ]]; then
    active_os="MacOS"
    echo " ✔ Active Operating System: ${active_os}"
    # TODO gotta check whether sound works in this case
    brew install pulseaudio
    brew services start pulseaudio

    sudo docker run -it -p 5000:5000 -e PULSE_SERVER=docker.for.mac.localhost -v ~/.config/pulse:/home/pulseaudio/.config/pulse frietz58/woz4u

  elif [[ "$OSTYPE" == "cygwin" ]]; then
    # * POSIX compatibility layer and Linux environment emulation for Windows
    active_os="Windows"
    # TODO gotta check whether the docker image works on container at all...
    echo " ✔ Active Operating System: ${active_os}"
    echo "We don't yet support docker on your OS. Please launch the docker image either from Linux or Mac."
    return 1

  elif [[ "$OSTYPE" == "msys" ]]; then
    # * Lightweight shell and GNU utilities compiled for Windows (part of MinGW)
    active_os="Windows"
    echo " ✔ Active Operating System: ${active_os}"
    echo "We don't yet support docker on your OS. Please launch the docker image either from Linux or Mac."
    return 1

  elif [[ "$OSTYPE" == "win32" ]]; then
    active_os="Windows"
    echo " ✔ Active Operating System: ${active_os}"
    echo "We don't yet support docker on your OS. Please launch the docker image either from Linux or Mac."
    return 1

  elif [[ "$OSTYPE" == "freebsd"* ]]; then
    active_os="FreeBSD"
    echo " ✔ Active Operating System: ${active_os}"
    echo "We don't yet support docker on your OS. Please launch the docker image either from Linux or Mac."
    return 1

  else
    active_os="Unknown"
    echo " ✔ Active Operating System: ${active_os}"
    echo "We don't yet support docker on your OS. Please launch the docker image either from Linux or Mac."
    return 1
  fi




