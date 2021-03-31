import io
import logging
import socketserver
import subprocess
from picamera import PiCamera
from threading import Condition
from http import server

global buttonDictionary

PAGE="""\
<!DOCTYPE html>
<html lang="en">
<head>
	<title>Camera Zero</title>
	<meta charset="utf-8">
	<meta name="apple-mobile-web-app-capable" content="yes">
	<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
	<meta name="application-name" content="Camera Zero">
	<meta name="theme-color" content="#000000">
	<style>
		body 
		{
			color: rgba(255, 255, 255, 1.0);
			font-family: 'Century Gothic', CenturyGothic, AppleGothic, sans-serif;
			margin: 0; 
			padding: 0;
		}

		.wrapper 
		{
			align-items: center; 
			background: rgba(8, 8, 8, 1.0); 
			display: flex; 
			flex-wrap: wrap;
			height: 100vh;
			justify-content: center; 
			width: 100vw; 
		}

		.stream
		{
			max-width: 960px;
			style="width: 100%; 
		}

		.controls
		{
			display: flex;
		}

		.control-group
		{
			margin: 0 8px;
		}

		.control-group label 
		{
			align-items: center;
			font-size: 12px;
			display: flex;
			justify-content: center;
			line-height: 12px;
			height: 24px;
			padding: 6px;
			text-align: center;
			width: 90px;
			
		}

		.control-button
		{
			border: solid 1px rgba(255, 255, 255, 1.0);
			border-radius: 4px;
			color: rgba(255, 255, 255, 1.0);
			display: inline-block;
			font-size: 36px;
			height: 42px;
			margin: 3px;
			text-align: center;
			text-decoration: none;
			width: 42px;
		}
	</style>
	<script>
		var controls = document.getElementsByClassName('control-button');
		controls.forEach(element => element.addEventListener('click', event => {
			var url = event.target.href;
			console.log(url);
			event.preventDefault();
		}));
	</script>
</head>
<body>
	<div class="wrapper">
		<div>
			<img src="stream.mjpg" class="stream" />
		</div>
		<div class="controls">
			<div class="control-group">
				<label>Capture</label>
				<div>
					<a href="/capture/photo" class="control-button">&#10030;</a>
					<a href="/capture/video" class="control-button">&#9679</a>
				</div>
			</div>
			<div class="control-group">
				<label>Shutter Speed</label>
				<div>
					<a href="/shutter/up" class="control-button">&#8853;</a>
					<a href="/shutter/down" class="control-button">&#8854;</a>
				</div>
			</div>
			<div class="control-group">
				<label>ISO</label>
				<div>
					<a href="/iso/up" class="control-button">&#8853;</a>
					<a href="/iso/down" class="control-button">&#8854;</a>
				</div>
			</div>
			<div class="control-group">
				<label>Exposure Compensation</label>
				<div>
					<a href="/ev/up" class="control-button">&#8853;</a>
					<a href="/ev/down" class="control-button">&#8854;</a>
				</div>
			</div>
			<div class="control-group">
				<label>Bracketing</label>
				<div>
					<a href="/bracket/up" class="control-button">&#8853;</a>
					<a href="/bracket/down" class="control-button">&#8854;</a>
				</div>
			</div>
		</div>
	</div>
</body>
</html>
"""

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
	def do_GET(self):
		global output
		global buttonDictionary
		if self.path == '/':
			content = PAGE.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content)
		elif self.path == '/stream.mjpg':
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
			except Exception as e:
				logging.warning(
					'Removed streaming client %s: %s',
					self.client_address, str(e))
		elif self.path == '/capture/photo':	
			buttonDictionary.update({'capture': True})
			print('click')
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


def startStream(camera, running, statusDictionary, parentButtonDictionary):
	global output
	global buttonDictionary
	buttonDictionary = parentButtonDictionary
	print(buttonDictionary['capture'])
	camera.resolution = (960, 540)
	#camera.framerate = 24
	with camera:
		output = StreamingOutput()
		camera.start_recording(output, format='mjpeg')
		hostname = subprocess.getoutput('hostname -I')
		url = 'http://' + str(hostname)
		print('\n Stream started: ' + url + '\n')
		try:
			address = ('', 80)
			server = StreamingServer(address, StreamingHandler)
			server.serve_forever()
		finally:
			camera.stop_recording()
			print('\n Stream ended \n')

def stopStream():
	with camera:
		camera.stop_recording()




