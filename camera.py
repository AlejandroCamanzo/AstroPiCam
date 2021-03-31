#/usr/bin/python3
from picamera import PiCamera
from pydng.core import RPICAM2DNG
from light import Light
import server
import datetime
import fractions
import os
import signal
import subprocess
import sys
import threading
import time


version = '2021.03.30'

camera = PiCamera()
PiCamera.CAPTURE_TIMEOUT = 1500
camera.resolution = camera.MAX_RESOLUTION
camera.sensor_mode = 3
camera.framerate = 30

dng = RPICAM2DNG()
running = False
statusDictionary = {'message': '', 'action': '', 'colorR': 0, 'colorG': 0, 'colorB': 0, 'colorW': 0}
buttonDictionary = {'switchMode': 0, 'shutterUp': False, 'shutterDown': False, 'isoUp': False, 'isoDown': False, 'evUp': False, 'evDown': False, 'bracketUp': False, 'bracketDown': False, 'capture': False, 'captureVideo': False, 'isRecording': False, 'lightR': 0, 'lightB': 0, 'lightG': 0, 'lightW': 0}
	
action = 'capture'

shutter = 'auto'
shutterLong = 30000
shutterLongThreshold = 1000
shutterShort = 0
defaultFramerate = 30

iso = 'auto'
isoMin = 100
isoMax = 1600

exposure = 'auto'

ev = 0
evMin = -25
evMax = 25

bracket = 0
bracketLow = 0
bracketHigh = 0

awb = 'auto'

outputFolder = 'dcim/'

timer = 0

raw = True



# === Echo Control =============================================================

def echoOff():
	subprocess.run(['stty', '-echo'], check=True)
def echoOn():
	subprocess.run(['stty', 'echo'], check=True)
def clear():
	subprocess.call('clear' if os.name == 'posix' else 'cls')
clear()



# === Functions ================================================================

def showInstructions(clearFirst = False, wait = 0):
	if clearFirst == True:
		clear()
	else:
		print(' ----------------------------------------------------------------------')

		time.sleep(wait)
	return

# ------------------------------------------------------------------------------

def setShutter(input, wait = 0):
	global shutter
	global shutterLong
	global shutterLongThreshold
	global shutterShort
	global defaultFramerate
	global statusDictionary
	
	if str(input).lower() == 'auto' or str(input) == '0':
		shutter = 0
	else:
		shutter = int(float(input))
		if shutter < shutterShort:
			shutter = shutterShort
		elif shutter > shutterLong:
			shutter = shutterLong 
	try:
		if camera.framerate == defaultFramerate and shutter > shutterLongThreshold:
			camera.framerate=fractions.Fraction(5, 1000)
		elif camera.framerate != defaultFramerate and shutter <= shutterLongThreshold:
			camera.framerate = defaultFramerate
	
		if shutter == 0:
			camera.shutter_speed = 0
			#print(str(camera.shutter_speed) + '|' + str(camera.framerate) + '|' + str(shutter))	
			print(' Shutter Speed: auto')
			statusDictionary.update({'message': 'Shutter Speed: auto'})
		else:
			camera.shutter_speed = shutter * 1000
			#print(str(camera.shutter_speed) + '|' + str(camera.framerate) + '|' + str(shutter))		
			floatingShutter = float(shutter/1000)
			roundedShutter = '{:.3f}'.format(floatingShutter)
			if shutter > shutterLongThreshold:
				print(' Shutter Speed: ' + str(roundedShutter)  + 's [Long Exposure Mode]')
				statusDictionary.update({'message': ' Shutter Speed: ' + str(roundedShutter)  + 's [Long Exposure Mode]'})
			else:
				print(' Shutter Speed: ' + str(roundedShutter) + 's')
				statusDictionary.update({'message': ' Shutter Speed: ' + str(roundedShutter) + 's'})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid Shutter Speed! ' + str(shutter) + '\n ' + str(ex))

# ------------------------------------------------------------------------------				

def setISO(input, wait = 0):
	global iso
	global isoMin
	global isoMax
	global statusDictionary

	if str(input).lower() == 'auto' or str(input) == '0':
		iso = 0
	else: 
		iso = int(input)
		if iso < isoMin:	
			iso = isoMin
		elif iso > isoMax:
			iso = isoMax	
	try:	
		camera.iso = iso
		#print(str(camera.iso) + '|' + str(iso))
		if iso == 0:
			print(' ISO: auto')
			statusDictionary.update({'message': ' ISO: auto'})
		else:	
			print(' ISO: ' + str(iso))
			statusDictionary.update({'message': ' ISO: ' + str(iso)})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid ISO Setting! ' + str(iso))

# ------------------------------------------------------------------------------

def setExposure(input, wait = 0):
	global exposure
	global statusDictionary

	exposure = input
	try:	
		camera.exposure_mode = exposure
		print(' Exposure Mode: ' + exposure)
		statusDictionary.update({'message': ' Exposure Mode: ' + exposure})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid Exposure Mode! ')
				
# ------------------------------------------------------------------------------

def setEV(input, wait = 0, displayMessage = True):
	global ev 
	global bracket
	global statusDictionary

	ev = input
	ev = int(ev)
	evPrefix = '+/-'
	if ev > 0:
		evPrefix = '+'
	elif ev < 0:
		evPrefix = ''
	try:
		camera.exposure_compensation = ev
		# print(str(camera.exposure_compensation) + '|' + str(ev))
		if displayMessage == True:
			print(' Exposure Compensation: ' + evPrefix + str(ev))
			statusDictionary.update({'message': ' Exposure Compensation: ' + evPrefix + str(ev)})
		time.sleep(wait)
		return
	except Exception as ex: 
		print(' WARNING: Invalid Exposure Compensation Setting! ')	
		
# ------------------------------------------------------------------------------				

def setBracket(input, wait = 0, displayMessage = True):
	global bracket
	global bracketLow
	global bracketHigh
	global evMax
	global evMin
	global statusDictionary

	bracket = int(input)
	try:
		bracketLow = camera.exposure_compensation - bracket
		if bracketLow < evMin:
			bracketLow = evMin
		bracketHigh = camera.exposure_compensation + bracket
		if bracketHigh > evMax:
			bracketHigh = evMax
		if displayMessage == True:
			print(' Exposure Bracketing: ' + str(bracket))
			statusDictionary.update({'message': ' Exposure Bracketing: ' + str(bracket)})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid Exposure Bracketing Value! ')

# ------------------------------------------------------------------------------

def setAWB(input, wait = 0):
	global awb
	global statusDictionary

	awb = input
	try:	
		camera.awb_mode = awb
		print(' White Balance Mode: ' + awb)
		statusDictionary.update({'message': ' White Balance Mode: ' + awb})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid Auto White Balance Mode! ')

# ------------------------------------------------------------------------------

def getFileName(timestamped = True, isVideo = False):
	now = datetime.datetime.now()
	datestamp = now.strftime('%Y%m%d')
	timestamp = now.strftime('%H%M%S')		
			
	if isVideo==True:
		extension = '.h264'
		return datestamp + '-' + timestamp + extension
	else:
		extension = '.jpg'
		if timestamped == True:
			return datestamp + '-' + timestamp + '-' + str(imageCount).zfill(2) + extension
		else:
			return datestamp + '-' + str(imageCount).zfill(8) + extension

# ------------------------------------------------------------------------------

def getFilePath(timestamped = True, isVideo = False):
	try:
		os.makedirs(outputFolder, exist_ok = True)
	except OSError:
		print (' ERROR: Creation of the output folder ' + outputFolder + ' failed! ')
		echoOn()
		quit()
	else:
		return outputFolder + getFileName(timestamped, isVideo)

# ------------------------------------------------------------------------------

def captureImage(filepath, raw = True):
	camera.capture(filepath, quality=100, bayer=raw)
	if raw == True:
		conversionThread = threading.Thread(target=convertBayerDataToDNG, args=(filepath,))
		conversionThread.start()

# ------------------------------------------------------------------------------		

def convertBayerDataToDNG(filepath):
	dng.convert(filepath)


# ------------------------------------------------------------------------------
def createControls():
	global running
	global statusDictionary	
	global buttonDictionary
	
	running = True
	server.startStream(camera, running, statusDictionary, buttonDictionary)
	
# -------------------------------------------------------------------------------
def darkMode():
	Light.off()
	

# === Image Capture ============================================================

controlsThread = threading.Thread(target=createControls)
controlsThread.start()


try:
	echoOff()
	imageCount = 1
	isRecording = False

	try:
		os.chdir('/home/pi') 
	except:
		pass
	
	def Capture(mode = 'persistent'):
		global shutter
		global shutterLong
		global shutterShort
		global iso
		global isoMin
		global isoMax
		global exposure
		global ev
		global evMin
		global evMax
		global bracket
		global awb
		global timer
		global raw
		global imageCount
		global isRecording
		global statusDictionary
		global buttonDictionary

		

		# print(str(camera.resolution))
		

		print('\n Camera ' + version )
		print('\n ----------------------------------------------------------------------')
		time.sleep(2)

		
		setShutter(shutter, 0)		
		setISO(iso, 0)
		setExposure(exposure, 0)
		setEV(ev, 0)
		setBracket(bracket, 0)
		setAWB(awb, 0)
		
		showInstructions(False, 0)
		
		while True:
			try:
					
				# Capture
				if buttonDictionary['capture'] == True:
					
					if mode == 'persistent':
						# Normal photo
						filepath = getFilePath(True)
						print(' Capturing image: ' + filepath + '\n')
						captureImage(filepath, raw)
						
						imageCount += 1
				
						if (bracket != 0):
							baseEV = ev
							# Take underexposed photo
							setEV(baseEV + bracketLow, 0, False)
							filepath = getFilePath(True)
							print(' Capturing image: ' + filepath + '  [' + str(bracketLow) + ']\n')
							captureImage(filepath, raw)
							imageCount += 1

							# Take overexposed photo
							setEV(baseEV + bracketHigh, 0, False)
							filepath = getFilePath(True)
							print(' Capturing image: ' + filepath + '  [' + str(bracketHigh) + ']\n')
							captureImage(filepath, raw)
							imageCount += 1						
							
							# Reset EV to base photo's value
							setEV(baseEV, 0, False)
							
					elif mode == 'timelapse':
						# Timelapse photo series
						if timer < 0:
							timer = 1
						while True:
							filepath = getFilePath(False)
							print(' Capturing timelapse image: ' + filepath + '\n')
							captureImage(filepath, raw)
							imageCount += 1
							time.sleep(timer) 	
							
					else:
						# Single photo and then exit
						filepath = getFilePath(True)
						print(' Capturing single image: ' + filepath + '\n')
						captureImage(filepath, raw)
						echoOn()
						break

					buttonDictionary.update({'capture': False})

				elif buttonDictionary['captureVideo'] == True:

					# Video
					if isRecording == False:
						server.stopStream(camera);		
						isRecording = True
						statusDictionary.update({'action': 'recording'})
						filepath = getFilePath(True, True)
						camera.resolution = (1920, 1080)
						print(' Capturing video: ' + filepath + '\n')
						statusDictionary.update({'message': ' Recording: Started '})
						buttonDictionary.update({'captureVideo': False})
						camera.start_recording(filepath, quality=20)
					else:
						isRecording = False
						statusDictionary.update({'action': ''})
						camera.stop_recording()
						camera.resolution = camera.MAX_RESOLUTION
						try:
							server.startStream(camera, running, statusDictionary, buttonDictionary)
						finally:
							print(' Capture complete \n')
						statusDictionary.update({'message': ' Recording: Stopped '})
						buttonDictionary.update({'captureVideo': False})
							
					time.sleep(1)

				# Shutter Speed	
				elif buttonDictionary['shutterUp'] == True:
					stopStream(camera)
					if shutter == 0:
						shutter = shutterShort
					if shutter > shutterShort and shutter <= shutterLong:					
						shutter = int(shutter / 1.5)
					setShutter(shutter, 0.25)
					buttonDictionary.update({'shutterUp': False})
					def startStream(camera, running, statusDictionary, buttonDictionary):
				elif buttonDictionary['shutterDown'] == True:
					stopStream(camera)
					if shutter == 0:						
						shutter = shutterLong
					elif shutter < shutterLong and shutter >= shutterShort:					
						shutter = int(shutter * 1.5)
					elif shutter == shutterShort:
						shutter = 0
					setShutter(shutter, 0.25)
					buttonDictionary.update({'shutterDown': False})
					def startStream(camera, running, statusDictionary, buttonDictionary):
				# ISO
				elif buttonDictionary['isoUp'] == True:
					if iso == 0:
						iso = isoMin
					if iso >= isoMin and iso < isoMax:					
						iso = int(iso * 2)
					setISO(iso, 0.25)
					buttonDictionary.update({'isoUp': False})
				elif buttonDictionary['isoDown'] == True:
					if iso == 0:
						iso = isoMax
					elif iso <= isoMax and iso > isoMin:					
						iso = int(iso / 2)
					elif iso == isoMin:
						iso = 0
					setISO(iso, 0.25)
					buttonDictionary.update({'isoDown': False})

				# Exposure Compensation
				elif buttonDictionary['evUp'] == True:
					if ev >= evMin and ev < evMax:					
						ev = int(ev + 1)
						setEV(ev, 0.25)
						buttonDictionary.update({'evUp': False})
				elif buttonDictionary['evDown'] == True:
					if ev <= evMax and ev > evMin:					
						ev = int(ev - 1)
						setEV(ev, 0.25)
						buttonDictionary.update({'evDown': False})
				# Exposure Bracketing
				elif buttonDictionary['bracketUp'] == True:
					if bracket < evMax:
						bracket = int(bracket + 1)
						setBracket(bracket, 0.25)
						buttonDictionary.update({'bracketUp': False})
				elif buttonDictionary['bracketDown'] == True:
					if bracket > 0:					
						bracket = int(bracket - 1)
						setBracket(bracket, 0.25)
						buttonDictionary.update({'bracketDown': False})
			except SystemExit:
				running = False
				time.sleep(5)				
				os.kill(os.getpid(), signal.SIGSTOP)
				sys.exit(0)
			except Exception as ex:
				print(str(ex))
				pass

	def CaptureAndUploadImage():
		Capture()
		time.sleep(1000)
		# Not yet implemented

	# print(' Action: ' + action)
	if action == 'capturesingle' or action == 'single':
		Capture('single')
	elif action == 'timelapse':
		Capture('timelapse')
	elif action == 'video':
		Capture('video')
	else:
		Capture()

except KeyboardInterrupt:
	darkMode()
	echoOn()
	sys.exit(1)
