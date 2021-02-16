#!/bin/bash

echo "updating repositories"

sudo apt update

echo "pip3 installing"

sudo apt install python3-pip -y

echo "fpdf2 installing"

pip3 install fpdf2

echo "kivy installing"

python3 -m pip install kivy[base]

echo "kivy dependancies"
sudo apt install pkg-config libgl1-mesa-dev libgles2-mesa-dev \
   libgstreamer1.0-dev \
   gstreamer1.0-plugins-{bad,base,good,ugly} \
   gstreamer1.0-{omx,alsa} libmtdev-dev \
   xclip xsel libjpeg-dev

echo "sdl2 installing"
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

echo "kivy-garden installing"

python3 -m pip install kivy_garden.graph --extra-index-url https://kivy-garden.github.io/simple/

echo "mpu6050 dependancies:"

sudo apt install python-smbus
sudo pip install mpu6050-raspberrypi