#!/bin/bash


sudo apt install python3-pyqt5 -y
sudo apt install python3-pip -y

pip3 install pyqtgraph

echo "mpu6050 dependancies:"

sudo apt install python-smbus
sudo pip install mpu6050-raspberrypi