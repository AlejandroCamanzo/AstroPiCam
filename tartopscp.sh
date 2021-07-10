#This scripts tar.gzs the images in dcim folder in order to send them to your windows machine using pscp
sudo tar -czvf ~/dcim/jpg.tar.gz ~/dcim/*.jpg
sudo tar -czvf ~/dcim/dng.tar.gz ~/dcim/*.dng

# in a windows cmd in the same network as the pi do:
# 'pscp pi@your.pi.ip.addr:/home/pi/dcim/jpg.tar.gz Downloads/jpg.tar.gz
# 'pscp pi@your.pi.ip.addr:/home/pi/dcim/dng.tar.gz Downloads/dngs.tar.gz
