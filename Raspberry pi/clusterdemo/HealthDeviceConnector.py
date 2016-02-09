#!/usr/bin/python

import time
import requests
import datetime
import websocket
from bluetooth import *
import datetime

hostMACAddress = ""
hostPort = PORT_ANY
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
backlog = 1
bufferSize = 1
DEFAULT_VALUE= 120

NONIN_PULSEOXYMETER_BT_ADDR = "00:1C:05:00:CC:15"
MYGLUCOHEALTH_GLUCOMETER_BT_ADDR = "00:13:7B:51:FE:2A"

ws = websocket.WebSocket()
ws.connect("ws://localhost:8001/")
#print 'Unable to connect to websocket #ws://localhost:8001/#'
#print 'Please start nodeJS websocket server...'

NO_PROXY = {
    'no': 'pass',
}

measurement = DEFAULT_VALUE
wsConnected = False

getSerialId = bytearray(6)
getSerialId[0] = 0x80
getSerialId[1] = 0x01
getSerialId[2] = 0xFE
getSerialId[3] = 0x09
getSerialId[4] = 0x81
getSerialId[5] = 0xF7
getSerialIdCommand = buffer(getSerialId, 0, 6)
getSerialIdResponse = ['']*18
getSerialIdResponseLen = len(getSerialIdResponse)
serialId = ['']*10

getAvailableRecordsNumber = bytearray(6)
getAvailableRecordsNumber[0] = 0x80
getAvailableRecordsNumber[1] = 0x01
getAvailableRecordsNumber[2] = 0xFE
getAvailableRecordsNumber[3] = 0x00
getAvailableRecordsNumber[4] = 0x81
getAvailableRecordsNumber[5] = 0xFE
getAvailableRecordsNumberCommand = buffer(getAvailableRecordsNumber, 0, 6)
getAvailableRecordsNumberResponse = ['']*7
getAvailableRecordsNumberResponseLen = len(getAvailableRecordsNumberResponse)

getLastRecord = bytearray(7)
getLastRecord[0] = 0x80
getLastRecord[1] = 0x02
getLastRecord[2] = 0xFD
getLastRecord[3] = 0x01
getLastRecord[4] = 0x00
getLastRecord[5] = 0x82
getLastRecord[6] = 0xFC
getLastRecordCommand = buffer(getLastRecord, 0, 7)
getLastRecordResponse = ['']*13
getLastRecordResponseLen = len(getLastRecordResponse)

def CreateServerSocket():
	servSocket = BluetoothSocket(RFCOMM)
	servSocket.bind((hostMACAddress, hostPort))
	servSocket.listen(backlog)
	print servSocket.getsockname()
	port = servSocket.getsockname()[1]
	advertise_service( servSocket, "MghGlucoseMeterServer", 
		service_id = uuid, 
		service_classes = [ uuid, SERIAL_PORT_CLASS ], 
		profiles = [ SERIAL_PORT_PROFILE ])
	print 'Waiting for connection on RFCOMM channel %d' % port
	#print 'Waiting for glucosemeter to connect...', hostMACAddress
	return servSocket
	
def SendGetSerialCommand():
	print '	Sending getSerialId command...'
	clientSocket.send(getSerialIdCommand)
	print '	GetSerialId command sent'
	
	for i in range(getSerialIdResponseLen):
		receivedByte = clientSocket.recv(bufferSize)
		getSerialIdResponse[i] = receivedByte #getSerialIdResponse.append(receivedByte)
		#print ("Received byte: ", receivedByte)
	#print 'GetSerialId response = ', getSerialIdResponse
		
	# Row data parsing
	for i in range(4, 14):
		serialId[i-4] = getSerialIdResponse[i]
	print 'Serial ID: ', ''.join(serialId)

def SendGetAvailableRecordsNumberCommand():
	print '	Sending getAvailableRecordsNumber command...'
	clientSocket.send(getAvailableRecordsNumberCommand)
	print '	GetAvailableRecordsNumber command sent'

	for i in range(getAvailableRecordsNumberResponseLen):
		receivedByte = clientSocket.recv(bufferSize)
		getAvailableRecordsNumberResponse[i] = receivedByte #getAvailableRecordsNumberResponse.append(receivedByte)
		#print("Received byte ", receivedByte)
		if receivedByte == "": break
	#print 'GetAvailableRecordsNumber response = ', getAvailableRecordsNumberResponse

	# Row data parsing
	availableRecordsNumber = ord(getAvailableRecordsNumberResponse[4])
	print 'Number of available records: ', availableRecordsNumber

def SendGetLastRecordCommand():
	#print '	Sending getLastRecord command...'
	clientSocket.send(getLastRecordCommand)
	#print '	GetLastRecord command sent'

	for i in range(getLastRecordResponseLen):
		receivedByte = clientSocket.recv(bufferSize)
		getLastRecordResponse[i] = receivedByte #getLastRecordResponse.append(receivedByte)
		#print("Received byte ", receivedByte)
		if receivedByte == "": break
	#print 'GetLastRecord response = ', getLastRecordResponse
	
	# Row data parsing
	return ParseRowData(getLastRecordResponse)

def ParseRowData(getLastRecordResponse):
	startingPayloadByte = 5
	lastRecord = [ord(x) for x in getLastRecordResponse]
	year = 2000 + (lastRecord[startingPayloadByte] >> 1)
	month = ((lastRecord[startingPayloadByte] & 0x01) << 3) + ((lastRecord[startingPayloadByte + 1] & 0xE0) >> 5)
	day = lastRecord[startingPayloadByte + 1] & 0x1F
	temp = (lastRecord[startingPayloadByte + 2] >> 2) & 0x3F
	value = ((lastRecord[startingPayloadByte + 2] & 0x03) << 8) + (lastRecord[startingPayloadByte + 3] & 0xFF)
	evnt = (lastRecord[startingPayloadByte + 4] & 0xF8) >> 3
	hour = ((lastRecord[startingPayloadByte + 4] & 0x07) << 2) + ((lastRecord[startingPayloadByte + 5] & 0xC0) >> 6)
	minute = lastRecord[startingPayloadByte + 5] & 0x3F
	ampm = 0
	print 'Glucose: ', value
	print 'Measured on {0}/{1}/{2} @ {3}:{4}'.format(str(day).zfill(2), str(month).zfill(2), year, str(hour).zfill(2), str(minute).zfill(2))
	
	return '{"Timestamp" : "' + str(datetime.datetime.now()) + '", "ServiceClass" : "BloodGlucoseMeter", "DeviceId" : "BLOODGLUCOSEMETER-1080826128", "Glucose" : ' + str(value) + '}'

def getPulseOximeterData(clientSocket):
	try:
		data = clientSocket.recv(1024)
		if len(data) == 0:
			print 'No data received... Please check measurement on device...'
		else:
			pulse = int(data[17].encode("hex"), 16)
			spo2 = int(data[19].encode("hex"), 16)
			print('Pulse Rate LSB: %d(BpM)' % pulse)
			print('SPO2: %d(%%)' % spo2)
			return '{"Timestamp" : "' + str(datetime.datetime.now()) + '", "ServiceClass" : "PulsiOximeter", "DeviceId" : "PULSEOXIMETER-501655666", "pulseOx" : ' + str(pulse) + ', "spO2" : ' + str(spo2) + '}'
	except IOError:
		print 'IO Error. Exiting...'
		pass

# MAIN PROGRAM
while True:
	serverSocket = CreateServerSocket()
	clientSocket, clientInfo = serverSocket.accept()
	print 'Accepted connection from ', clientInfo
	if clientInfo[0] == NONIN_PULSEOXYMETER_BT_ADDR:
		print
		print '            *** Nonin PulseOxymeter ***'
		print '---------------------------------------------------'
		measurement = getPulseOximeterData(clientSocket)
		print '***************************************************'
		clientSocket.close()
                serverSocket.close()
		ws.send(measurement)
                print 'data sent to localhost'
                result = ws.recv()
                print result
	elif clientInfo[0] == MYGLUCOHEALTH_GLUCOMETER_BT_ADDR:
		print
		print '        *** Myglucohealth GlucoseMeter ***'
		try:
			measurement = DEFAULT_VALUE
			print
			print '---------------------------------------------------'
			SendGetSerialCommand()
			print '***************************************************'

			time.sleep(0.5)
			"""
			print
			print '---------------------------------------------------'
			SendGetAvailableRecordsNumberCommand()
			print '***************************************************'
		
			time.sleep(0.5)
			"""
			print '---------------------------------------------------'
			measurement = SendGetLastRecordCommand()
			print '***************************************************'
		
			clientSocket.close()
			serverSocket.close()
			ws.send(str(measurement))
                	print 'data sent to localhost'
                	result = ws.recv()
                	print result

		except:
			print 'Exception. Closing sockets'
			clientSocket.close()
			serverSocket.close()
			print 'All done'
	else:
		print 'Unknown device. Abort...'
		clientSocket.close()
		serverSocket.close()
	time.sleep(7)	
