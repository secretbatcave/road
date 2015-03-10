#!/usr/bin/env python

import gps
import time
import Queue
import sqlite3
import logging
import picamera
import threading
import XLoBorg as xlo

logging.basicConfig(level=logging.WARN, format='(%(threadName)-10s) %(message)s')
log = logging


class road:
	def __init__(self):
		xlo.Init()
		self.q			= Queue.Queue(maxsize=200)
		self.run 		= 1
		self.gpsHandle		= gps.gps(mode=gps.WATCH_ENABLE)
		self.journeyID		= 4 #set an ID somewhere to define each trip.
		self.lastGpsFixID	= 0
		self.threads		= []
		self.bump		= 0
		self.location		= 0
		self.photoDir		= '/disk/photos/' #must exsist
		self.photoInterval	= 60 #seconds
	def trackPhoto(self):
		'''This function takes a photos every n seconds (defined by photoInterval)
		it then dumps it into the specified directory (photodir) 
		'''
		while self.run:
			with picamera.PiCamera as camera:
				try:
					currentPic = open(self.photoDir + str(time.time()) + '.jpg')
					camera.capture(currentPic)
					currentPic.close()
					log.debug('Photo taken and saved')
				except Exception, e:
					print str(e)
					
				time.sleep(self.photoInterval)
	def trackGPS(self):
		'''This function listens to GPSD and dumps the data into the database
		it maintains some shortcut variables to make the insertion of Acclerometer data
		quicker/easier... possibly.
		'''
		while self.run:
			try:
				currentFix = self.gpsHandle.next()
				log.debug("GPS:")
				log.debug(currentFix)
				if currentFix['class'] == 'TPV' and hasattr(currentFix, 'lat'):
					#then we have teh dators
					try:
						self.q.put("INSERT INTO gpsData VALUES(NULL, '%s', %s, %s, %s, %s, %s)" % (currentFix.time,currentFix.lat,currentFix.lon,currentFix.alt,currentFix.speed,currentFix.epx))
						self.location = currentFix
					except Exception, e:
						log.info(e)
			except StopIteration:
				pass
				log.error("Gps say stop iterating")
		return True
	def trackBump(self):
		'''Tracks the bumpy bumpy on the roady roady and puts it into dave the database.
		and junk.
		'''
		while self.run:
			x, y, z = xlo.ReadAccelerometer()
			self.q.put("INSERT INTO bump VALUES(NULL, %f, %f, %f, %f, %d, (SELECT MAX(id) FROM gpsData))"%(time.time(),x,y,z,self.journeyID))
			self.bump = [x,y,z]
			time.sleep(0.025)
	def database(self):
		'''Sits in its own thread monitoring self.q and updating the database
		when it gets data. This is to get round py-sqlite's refusal to run in
		other threads than the one it's created in.
		'''
		databasecon = sqlite3.connect('database.db', isolation_level=None)
		db = databasecon.cursor()
		while self.run:
			query = self.q.get(1)
			log.debug(query)
			db.execute(query)
			log.info("DB inserted")

		database.close()
		log.debug('Database closed')

	def start(self):
		'''This is the function that starts all the threads needed to
		run the Database, acceleromiter, camera and GPS
		'''

		databaseThread = threading.Thread(target=self.database, name='Database handler')
		databaseThread.setDaemon(True)
		databaseThread.start()
		log.debug('Db started')
		self.threads.append(databaseThread)
		
		photoThread = threading.Thread(target=self.trackPhoto, name='Photo handler')
		photoThread.setDaemon(True)
		photoThread.start()
		log.debug('Photo thread starting')
		self.threads.append(photoThread)
		§
		gpsThread = threading.Thread(target=self.trackGPS, name='GPS handler')
		gpsThread.setDaemon(True)#don't wait for this thread before quitting.
		gpsThread.start()
		self.threads.append(gpsThread)
		log.debug("GPS started")

		while self.run and self.lastGpsFixID !=0:
			#wait for the GPS to get an initial fixe before we start streamining data
			time.sleep(0.5)
			log.debug("Waiting for first fix")

		log.debug("got first fix")
		bumpThread = threading.Thread(target=self.trackBump, name='Bump catcher')
		bumpThread.setDaemon(True)
		bumpThread.start()
		self.threads.append(bumpThread)
		log.debug("Bump thread running")


	


