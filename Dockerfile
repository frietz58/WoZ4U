# base image
FROM python:2.7

# Download latest listing of available packages:
RUN apt-get -y update

# Upgrade already installed packages:
RUN apt-get -y upgrade

# Install package required for sound steam
RUN apt-get -y install \ 
	libportaudio2 \
	libasound-dev
	

# set workdir for container
WORKDIR /WoZ4U

# add naoqi OS
ADD https://community-static.aldebaran.com/resources/2.5.10/Python%20SDK/pynaoqi-python2.7-2.5.7.1-linux64.tar.gz .
RUN tar -xf pynaoqi-python2.7-2.5.7.1-linux64.tar.gz

# set environment variables for python to find naoqi api
ENV PYTHONPATH=/WoZ4U/pynaoqi-python2.7-2.5.7.1-linux64/lib/python2.7/site-packages
ENV DYLD_LIBRARY_PATH=/WoZ4U/pynaoqi-python2.7-2.5.7.1-linux64/lib


# add requirements to container
COPY requirements.txt .

# install requirements in container
RUN pip install -r requirements.txt

# copy all the required files and folders into container
COPY __init__.py .
COPY config.yaml .
COPY server.py .
COPY simple_sound_stream.py .
COPY utils.py .
COPY static ./static/
COPY templates ./templates/

CMD python server.py
