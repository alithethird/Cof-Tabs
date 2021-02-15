#!/bin/bash

echo "pip3 installing"

sudo apt install python3-pip -y

echo "fpdf2 installing"

pip3 install fpdf2

echo "kivy installing"

python3 -m pip install kivy[base]

echo "kivy-garden installing"

python3 -m pip install kivy_garden.graph --extra-index-url https://kivy-garden.github.io/simple/

echo "mpu6050 dependancies:"

sudo apt install python-smbus
sudo pip install mpu6050-raspberrypi