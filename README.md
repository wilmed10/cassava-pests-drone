#**Drone system for pest detection in cassava crops with custom tensorflow lite model**
This project was designed to perform early detection of pests (gall flies, weeds and mosaic) in cassava crops with the help of a drone. The development of the project is detailed below as follows:
1. Drone assembly.
2. Training of the custom model with tensorflow lite.
3. System configuration on Raspberry pi 4.

##Drone assembly
![drone](/assets/dron.jpg)
The drone used for this purpose is 10 inches, so it is able to carry the case with the Raspberry and the battery, the components needed to assemble the drone are the following:
*Frame 450
*10 inch propellers
*APM 2.8
*M8N GPS module
*40 amp ESC
*D2030 1000kv brushless motor
*Flysky FS-i6X
*FS-IA6B receiver
*3S 5000mAh battery
*BEC
The connections for the assembly of the drone are the following:
![drone connections](/assets/conexionDron.jpg)
https://www.youtube.com/watch?v=eSC5QJk-ODk&t=751s This video serves as a guide for assembling the components and configuring the flight controller.

##**Custom model training with tensorflow lite (Efficientdet_lite0)**
To train the model with tensorflow lite, the efficientdet_lite0 model was chosen. To do this, it is necessary to:
Create a virtual environment or directly install the `Python 3.9.0` version on our PC https://www.python.org/downloads/release/python-390/ and run the commands in the cmd
```
pip install –upgrade pip
pip install numpy==1.23.4
pip install tensorflow=2.8.0
pip install tlite-model-maker
```
With this we have enough to run `./train/efficientdet_lite0_train.py` once we have the dataset ready.
To do this, it is necessary to tag the images, either with makesense.ai or roboflow.com, and finally export the dataset in ***PASCAL VOC*** format so that the folder is structured as follows:
```
.
|-	train
|	|- img1.jpg
|	|- img1.xml
|-	validate
|	|- img5.jpg
|	|- img5.xml
```
With the prerequisites installed and the dataset ready we can now run the script that generates the model as `model.tflite`
```
python efficientdet_lite0_train.py
```

##**System configuration on Raspberry pi 4**
The detection system is configured to run on a Raspberry Pi 4 board with Raspberry Pi OS (64-bit), to continue with the system configuration, we follow the following steps:
```
# for update and auto-upgrade all packages
sudo apt update && sudo apt upgrade -y
```
###Camera configuration
```
# Arducam 64MP HawkEye prerequisites
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh
./install_pivariety_pkgs.sh -p libcamera_dev
./install_pivariety_pkgs.sh -p libcamera_apps
```
Modify .Config file
```
sudo nano /boot/config.txt 
#Find the line: [all], add the following item under it:
dtoverlay=arducam-64mp
#Save and reboot.
```
###Install `gpsd`
```
sudo apt update
sudo apt install gpsd gpsd-clients python3-gps -y
# config gpsd
sudo nano /etc/default/gpsd
# modify the lines:
# Paths to GPS devices
DEVICES="/dev/ttyUSB0"  # Change to your GPS port

#reboot and enable gpsd
sudo systemctl stop gpsd.socket
sudo systemctl disable gpsd.socket
sudo systemctl enable gpsd
sudo systemctl start gpsd
```
###Install Tflite
```
#clone repository
git clone https://github.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi.git
cd TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi

#install dependency
chmod +x get_pi_requirements.sh
./get_pi_requirements.sh
```
###Drone system
To run the drone's operating code, you need to paste the following scripts into the cloned folder on the Raspberry Pi board:
*./system/drone.py
*./system/gpsDrone.py
Additionally, you need to paste the pre-trained model (.tflite) into the `Sample_TFLite_model` folder
```
# to run the drone code, go to the tflite folder and run the command
python3 drone.py
```
###Communication System
![drone communication system](/assets/sistemaDron.jpg)
Once we execute the operation script on the Raspberry Pi, it is necessary to compile and upload the code `./system/communication.ino` to the ESP8266 or ESP32 board to carry out communication between the drone and the remote user.