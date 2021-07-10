# This script will install the camera, dng support, and any required prerequisites.
cd ~
echo -e ''
echo -e '\033[32mCamera Remote [Installation Script] \033[0m'
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e ''
echo -e '\033[93mUpdating package repositories... \033[0m'
sudo apt update

echo ''
echo -e '\033[93mInstalling prerequisites... \033[0m'
sudo apt install -y git python3 python3-pip python3-picamera
# sudo pip3 install RPi.GPIO adafruit-circuitpython-neopixel --force

echo ''
echo -e '\033[93mInstalling DNG support... \033[0m'
sudo git clone https://github.com/schoolpost/PyDNG.git
sudo chown -R $USER:$USER PyDNG
cd PyDNG
sudo pip3 install src/.
cd ~
sudo rm -Rf PyDNG

echo ''
echo -e '\033[93mInstalling AstroPiCam... \033[0m'
cd ~
sudo rm -Rf ~/AstroPiCam
sudo git clone https://github.com/AlejandroCamanzo/AstroPiCam
sudo mkdir -p ~/AstroPiCam/logs
sudo chown -R $USER:$USER AstroPiCam
cd AstroPiCam
sudo chmod +x camera.py
sudo chmod +x server.py

echo ''
echo -e '\033[93mDownloading color profiles... \033[0m'
cd ~
sudo rm -Rf ~/AstroPiCam/profiles
mkdir ~/AstroPiCam/profiles
sudo chown -R $USER:$USER ~/AstroPiCam/profiles
wget -q https://github.com/davidplowman/Colour_Profiles/raw/master/imx477/PyDNG_profile.dcp -O ~/AstroPiCam/profiles/basic.dcp
wget -q https://github.com/davidplowman/Colour_Profiles/raw/master/imx477/Raspberry%20Pi%20High%20Quality%20Camera%20Lumariver%202860k-5960k%20Neutral%20Look.dcp -O ~/AstroPiCam/profiles/neutral.dcp
wget -q https://github.com/davidplowman/Colour_Profiles/raw/master/imx477/Raspberry%20Pi%20High%20Quality%20Camera%20Lumariver%202860k-5960k%20Skin%2BSky%20Look.dcp -O ~/AstroPiCam/profiles/skin-and-sky.dcp

echo ''
echo -e '\033[93mSetting up alias... \033[0m'
cd ~
sudo touch ~/.bash_aliases
sudo sed -i '/\b\(function AstroPiCam\)\b/d' ~/.bash_aliases
sudo sed -i '$ a function AstroPiCam { sudo python3 ~/AstroPiCam/camera.py "$@"; }' ~/.bash_aliases
# This source statements are UNTESTED
source .bashrc
source .bash_aliases
echo -e 'Please ensure that your camera and I2C interfaces are enabled in raspi-config before proceeding.'

echo ''
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e '\033[32mInstallation completed. \033[0m'
echo ''
sudo rm install-camera.sh
bash
