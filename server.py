import io
import logging
import socketserver
import subprocess
import codecs
from light import Light
from picamera import PiCamera
from threading import Condition
from http import server

global buttonDictionary

# Import HTML page from file, better for maintenance and changes
PAGE = codecs.open("main.html", 'r', 'utf-8')

class StreamingOutput(object):
	def __init__(self):
		self.frame = None
		self.buffer = io.BytesIO()
		self.condition = Condition()

	def write(self, streamBuffer):
		if streamBuffer.startswith(b'\xff\xd8'):
			self.buffer.truncate()
			with self.condition:
				self.frame = self.buffer.getvalue()
				self.condition.notify_all()
			self.buffer.seek(0)
		return self.buffer.write(streamBuffer)


class StreamingHandler(server.BaseHTTPRequestHandler):
	def log_message(self, format, *args):
		pass

	def do_GET(self):
		global output
		global statusDictionary
		global buttonDictionary
		if self.path == '/':
			contentEncoded = PAGE.read().encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path == '/stream.mjpg' or self.path == '/blank.jpg':
			self.send_response(200)
			self.send_header('Age', 0)
			self.send_header('Cache-Control', 'no-cache, private')
			self.send_header('Pragma', 'no-cache')
			self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
			self.end_headers()
			try:
				while True:
					with output.condition:
						output.condition.wait()
						frame = output.frame
					self.wfile.write(b'--FRAME\r\n')
					self.send_header('Content-Type', 'image/jpeg')
					self.send_header('Content-Length', len(frame))
					self.end_headers()
					self.wfile.write(frame)
					self.wfile.write(b'\r\n')
			except Exception as ex:
				pass
		elif self.path == '/status':
			content = statusDictionary['message']
			if len(content) == 0:
				content = "Ready"
			contentEncoded = content.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path.startswith('/control/'):
			if self.path == '/control/capture/photo':	
				buttonDictionary.update({'capture': True})

			elif self.path == '/control/capture/video':	
				buttonDictionary.update({'captureVideo': True})

			elif self.path == '/control/shutter/up':	
				buttonDictionary.update({'shutterUp': True})

			elif self.path == '/control/shutter/down':	
				buttonDictionary.update({'shutterDown': True})

			elif self.path == '/control/iso/up':	
				buttonDictionary.update({'isoUp': True})

			elif self.path == '/control/iso/down':	
				buttonDictionary.update({'isoDown': True})

			elif self.path == '/control/ev/up':	
				buttonDictionary.update({'evUp': True})

			elif self.path == '/control/ev/down':	
				buttonDictionary.update({'evDown': True})

			elif self.path == '/control/bracket/up':	
				buttonDictionary.update({'bracketUp': True})

			elif self.path == '/control/bracket/down':	
				buttonDictionary.update({'bracketDown': True})

			elif self.path == '/control/exit':	
				buttonDictionary.update({'exit': True})

			elif self.path == '/control/trackball':	
				buttonDictionary.update({'trackball': True})

			elif self.path == '/control/light/all/on':	
				buttonDictionary.update({'lightW': 255})
				buttonDictionary.update({'lightR': 255})
				buttonDictionary.update({'lightG': 255})
				buttonDictionary.update({'lightB': 255})

			elif self.path == '/control/light/all/off':	
				buttonDictionary.update({'lightW': 0})
				buttonDictionary.update({'lightR': 0})
				buttonDictionary.update({'lightG': 0})
				buttonDictionary.update({'lightB': 0})

			elif self.path == '/control/light/white/up':	
				if buttonDictionary['lightW'] < 255:
					buttonDictionary.update({'lightW': buttonDictionary['lightW'] + 1})
				else: 
					buttonDictionary.update({'lightW': 0})

			elif self.path == '/control/light/white/down':	
				if buttonDictionary['lightW'] > 0:
					buttonDictionary.update({'lightW': buttonDictionary['lightW'] - 1})
				else: 
					buttonDictionary.update({'lightW': 255})

			elif self.path == '/control/light/red/up':	
				if buttonDictionary['lightR'] < 255:
					buttonDictionary.update({'lightR': buttonDictionary['lightR'] + 1})
				else: 
					buttonDictionary.update({'lightR': 0})

			elif self.path == '/control/light/red/down':	
				if buttonDictionary['lightR'] > 0:
					buttonDictionary.update({'lightR': buttonDictionary['lightR'] - 1})
				else: 
					buttonDictionary.update({'lightR': 255})

			elif self.path == '/control/light/green/up':	
				if buttonDictionary['lightG'] < 255:
					buttonDictionary.update({'lightG': buttonDictionary['lightG'] + 1})
				else: 
					buttonDictionary.update({'lightG': 0})

			elif self.path == '/control/light/green/down':	
				if buttonDictionary['lightG'] > 0:
					buttonDictionary.update({'lightG': buttonDictionary['lightG'] - 1})
				else: 
					buttonDictionary.update({'lightG': 255})

			elif self.path == '/control/light/blue/up':	
				if buttonDictionary['lightB'] < 255:
					buttonDictionary.update({'lightB': buttonDictionary['lightB'] + 1})
				else: 
					buttonDictionary.update({'lightB': 0})

			elif self.path == '/control/light/blue/down':	
				if buttonDictionary['lightB'] > 0:
					buttonDictionary.update({'lightB': buttonDictionary['lightB'] - 1})
				else: 
					buttonDictionary.update({'lightB': 255})

			Light.updateLight(buttonDictionary)
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', 0)
			self.end_headers()
		elif self.path == '/favicon.ico':
			self.send_response(200)
			self.send_header('Content-Type', 'image/x-icon')
			self.send_header('Content-Length', 0)
			self.end_headers()
		else:
			self.send_error(404)
			self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True


def startStream(camera, running, parentStatusDictionary, parentButtonDictionary):
	global output
	global statusDictionary 
	global buttonDictionary
	statusDictionary = parentStatusDictionary
	buttonDictionary = parentButtonDictionary
	camera.resolution = (1920, 1080)
	camera.framerate = 30

	output = StreamingOutput()
	camera.start_recording(output, format='mjpeg')
	hostname = subprocess.getoutput('hostname -I')
	url = 'http://' + str(hostname)
	print('\n Remote Interface: ' + url + '\n')
	try:
		address = ('', 80)
		server = StreamingServer(address, StreamingHandler)
		server.allow_reuse_address = True
		server.logging = False
		server.serve_forever()
	finally:
		camera.stop_recording()
		print('\n Stream ended \n')


def resumeStream(camera, running, parentStatusDictionary, parentButtonDictionary):
	global output
	global statusDictionary 
	global buttonDictionary
	statusDictionary = parentStatusDictionary
	buttonDictionary = parentButtonDictionary
	camera.resolution = (1920, 1080)
	camera.framerate = 30
	output = StreamingOutput()
	camera.start_recording(output, format='mjpeg')
	print(" Resuming preview... ")


def pauseStream(camera):
	try:
		camera.stop_recording()
		print(" Pausing preview... ")
	except Exception as ex:
		print(str(ex))
		pass
