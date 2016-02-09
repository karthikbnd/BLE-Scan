#!/usr/bin/python

import sys
import dbus
import re
import dbus.service
import dbus.mainloop.glib
import os
import glib
import time
from test_healthd_parser import *
# H&C
import requests
import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parse, parseString

dump_prefix = "XML"

# H&C
OMRON_SCALE_BT_ADDR = "00:22:58:38:9b:da"
OMRON_SPHYGMOMANOMETER_BT_ADDR = "00:22:58:35:c2:ab"
NONIN_PULSEOXYMETER_BT_ADDR = "00:1c:05:00:a1:4a"
devAddr = "00:00:00:00:00:00"

#virtualizerIp = "10.38.102.176"		# Virtualizer test
virtualizerIp = "192.168.100.100"	# Virtualizer demo H&C
virtualizerPort = "8000"
virtualizerService = "http://" + virtualizerIp + ":" + virtualizerPort + "/HiLife/HealthAndCare/BluetoothHealthcareDeviceUpdate"
VIRTUALIZER_UPDATE = True

NO_PROXY = {
    'no': 'pass',
}

system_ids = {}

def get_system_id(path, xmldata):
	if path in system_ids:
		return system_ids[path]
	sid = ""
	sid = get_system_id_from_mds(xmldata)
	if sid:
		system_ids[path] = sid
	return sid
	
def dump(path, suffix, xmldata):
	xmldata = beautify(xmldata)
	rsid = get_system_id(path, None)
	if len(rsid) > 4:
		rsid = rsid[-4:]
	if rsid:
		rsid += "_"
	f = open(dump_prefix + "_" + rsid + suffix + ".xml", "w")
	f.write(xmldata)
	f.close()

gsdr = {0: "Success", 1: "Segment unknown", 2: "Fail, try later",
	3: "Fail, segment empty", 512: "Fail, other"}

def getsegmentdata_response_interpret(i):
	try:
		s = gsdr[i]
	except KeyError:
		s = "Unknown fail code"
	return s

pmstore_handle = -1
pmsegment_instance = -1
clear_segment = 0
get_segment = 0
get_pmstore = 0
get_mds = 0
set_time = 0
interpret_data = 0

class Agent(dbus.service.Object):
        
	@dbus.service.method("com.signove.health.agent", in_signature="ss", out_signature="")
	def Connected(self, dev, addr):
		global devAddr
		print
		print "Connected from addr %s, dev %s" % (addr, dev)

		# H&C
		devAddr = addr
		if devAddr == NONIN_PULSEOXYMETER_BT_ADDR:
			print "*** Nonin PulseOxymeter"
		elif devAddr == OMRON_SCALE_BT_ADDR:
			print "*** Omron Scale"
		elif devAddr == OMRON_SPHYGMOMANOMETER_BT_ADDR:
			print "*** Omron SphygmoManometer"
		else:
			device = "Unknown device"
		
		# Convert path to an interface
		dev = bus.get_object("com.signove.health", dev)
		dev = dbus.Interface(dev, "com.signove.health.device")

		glib.timeout_add(0, do_something, dev)

	@dbus.service.method("com.signove.health.agent", in_signature="ss", out_signature="")
	def Associated(self, dev, xmldata):
		print
		print "Associated dev %s: XML with %d bytes" % (dev, len(xmldata))

		print "System ID: %s" % get_system_id(dev, xmldata)
		dump(dev, "associated", xmldata)
		
		# Convert path to an interface
		devpath = dev
		dev = bus.get_object("com.signove.health", dev)
		dev = dbus.Interface(dev, "com.signove.health.device")

		glib.timeout_add(0, getConfiguration, dev, devpath)
		if clear_segment == 1:
			glib.timeout_add(1000, clearSegment, dev, pmstore_handle, pmsegment_instance)
			return
		elif clear_segment == 2:
			glib.timeout_add(1000, clearAllSegments, dev, pmstore_handle)
			return

		if get_mds:
			glib.timeout_add(1000, requestMdsAttributes, dev)
		if set_time:
			glib.timeout_add(800, setTime, dev)
		if get_pmstore:
			glib.timeout_add(2000, getPMStore, dev, pmstore_handle)
			glib.timeout_add(3000, getSegmentInfo, dev, pmstore_handle)
		if get_segment:
			glib.timeout_add(5000, getSegmentData, dev, pmstore_handle, pmsegment_instance)

	@dbus.service.method("com.signove.health.agent", in_signature="ss", out_signature="")
	def MeasurementData(self, dev, xmldata):
		global devAddr
		print
		print "MeasurementData dev %s" % dev
		if interpret_data:
			Measurement(DataList(xmldata)).describe()
		else:
			print "=== Data: ", xmldata
			
			# H&C data parsing and upload to virtualizer
			deviceData = parseDeviceXmlData(xmldata)
			
			if devAddr == NONIN_PULSEOXYMETER_BT_ADDR:
				for i in range(len(deviceData)):
					if i == 0:
						satO2 = deviceData[i]
						satO2 = satO2.split(".")[0]
						print "SatO2: " + satO2 + " %"
					elif i == 1:
						pulseOx = deviceData[i]
						pulseOx = pulseOx.split(".")[0]
						print "Pulse: " + pulseOx + " BPM"
						
				xmlDataToPost = createPulseoxymeterXmlToPost(pulseOx, satO2)
									
			elif devAddr == OMRON_SCALE_BT_ADDR:
				for i in range(len(deviceData)):
					if i == 0:
						weight = deviceData[i]
						print "Weight: " + weight + " kg"
					elif i == 2:
						bmi = deviceData[i]
						print "Body Mass Index (BMI): " + bmi
					elif i == 3:
						bodyFat = deviceData[i]
						print "Body Fat: " + bodyFat
					elif i == 4:
						restingMetabolism = deviceData[i]
						print "Resting Metabolism: " + restingMetabolism + " cal"
					elif i == 5:
						visceralFat = deviceData[i]
						print "Visceral Fat: " + visceralFat
					elif i == 6:
						bodyAge = deviceData[i]
						print "Body Age: " + bodyAge
					elif i == 7:
						skeletalMuscle = deviceData[i]
						print "Skeletal Muscle: " + skeletalMuscle + " %"

				xmlDataToPost = createScaleXmlToPost(weight, bodyFat, skeletalMuscle)
			
			elif devAddr == OMRON_SPHYGMOMANOMETER_BT_ADDR:
				for i in range(len(deviceData)):
					if i == 0:
						pulse = deviceData[i]
						pulse = pulse.split(".")[0]
						print "Pulse: " + pulse + " BPM"
					elif i == 2:
						sys = deviceData[i]
						sys = sys.split(".")[0]
						print "Systolic Pressure: " + sys + " mmHg"
					elif i == 3:
						dia = deviceData[i]
						dia = dia.split(".")[0]
						print "Diastolic Pressure: " + dia + " mmHg"
				
				xmlDataToPost = createSphygmomanometerXmlToPost(sys, dia, pulse)
			
			print xmlDataToPost
			
			if VIRTUALIZER_UPDATE:
				updateVirtualizer(xmlDataToPost)
				
	@dbus.service.method("com.signove.health.agent", in_signature="sis", out_signature="")
	def PMStoreData(self, dev, pmstore_handle, xmldata):
		print
		print "PMStore dev %s handle %d" % (dev, pmstore_handle)
		if interpret_data:
			PMStore(DataList(xmldata)).describe()
		else:
			print "=== Data: XML with %d bytes" % len(xmldata)
		dump(dev, "pmstore_%d" % pmstore_handle, xmldata)

	@dbus.service.method("com.signove.health.agent", in_signature="sis", out_signature="")
	def SegmentInfo(self, dev, pmstore_handle, xmldata):
		print
		print "SegmentInfo dev %s PM-Store handle %d" % (dev, pmstore_handle)
		if interpret_data:
			SegmentInfo(DataList(xmldata)).describe()
		else:
			print "=== XML with %d bytes" % len(xmldata)
		dump(dev, "segmentinfo_%d" % pmstore_handle, xmldata)

	@dbus.service.method("com.signove.health.agent", in_signature="siii", out_signature="")
	def SegmentDataResponse(self, dev, pmstore_handle, pmsegment, response):
		print
		print "SegmentDataResponse dev %s PM-Store handle %d" % (dev, pmstore_handle)
		print "=== InstNumber %d" % pmsegment
		print "=== Response %s" % getsegmentdata_response_interpret(response)
		if response != 0 and pmsegment < 7:
			dev = bus.get_object("com.signove.health", dev)
			dev = dbus.Interface(dev, "com.signove.health.device")
			glib.timeout_add(0, getSegmentData, dev, pmstore_handle, pmsegment + 1)

	@dbus.service.method("com.signove.health.agent", in_signature="siis", out_signature="")
	def SegmentData(self, dev, pmstore_handle, pmsegment, xmldata):
		print
		print "SegmentData dev %s PM-Store handle %d inst %d" % \
			(dev, pmstore_handle, pmsegment)
		if interpret_data:
			SegmentData(DataList(xmldata)).describe()
		else:
			print "=== Data: %d bytes XML" % len(xmldata)
		dump(dev, "segmentdata_%d_%d" % (pmstore_handle, pmsegment), xmldata)

	@dbus.service.method("com.signove.health.agent", in_signature="siii", out_signature="")
	def SegmentCleared(self, dev, pmstore_handle, pmsegment, retstatus):
		print
		print "SegmentCleared dev %s PM-Store handle %d" % (dev, pmstore_handle)
		print "=== InstNumber %d retstatus %d" % (pmsegment, retstatus)
		print
		
	@dbus.service.method("com.signove.health.agent", in_signature="ss", out_signature="")
	def DeviceAttributes(self, dev, xmldata):
		print
		print "DeviceAttributes dev %s" % dev
		if interpret_data:
			DeviceAttributes(DataList(xmldata)).describe()
		else:
			print "=== Data: XML with %d bytes" % len(xmldata)
		dump(dev, "attributes", xmldata)

	@dbus.service.method("com.signove.health.agent", in_signature="s", out_signature="")
	def Disassociated(self, dev):
		print
		print "Disassociated dev %s" % dev

	@dbus.service.method("com.signove.health.agent", in_signature="s", out_signature="")
	def Disconnected(self, dev):
		print
		print "Disconnected %s" % dev

def requestMdsAttributes (dev):
	dev.RequestDeviceAttributes()
	return False

def setTime(dev):
	print "Setting time to now"
	dev.SetTime(time.time())
	return False

def getConfiguration(dev, devpath):
	config = dev.GetConfiguration()
	print
	print "Configuration: XML with %d bytes" % len(config)
	print
	dump(devpath, "config", config)
	if interpret_data:
		Configuration(DataList(config)).describe()
	return False

def getSegmentInfo(dev, handle):
	ret = dev.GetSegmentInfo(handle)
	print
	print "GetSegmentInfo ret %d" % ret
	print
	return False

def getSegmentData(dev, handle, instance):
	ret = dev.GetSegmentData(handle, instance)
	print
	print "GetSegmentData ret %d" % ret
	print
	return False

def clearSegment(dev, handle, instance):
	ret = dev.ClearSegment(handle, instance)
	print
	print "ClearSegment ret %d" % ret
	print
	return False

def clearAllSegments(dev, handle):
	ret = dev.ClearAllSegments(handle)
	print
	print "ClearAllSegments ret %d" % ret
	print
	return False

def getPMStore(dev, handle):
	ret = dev.GetPMStore(handle)
	print
	print "GetPMStore ret %d" % ret
	print
	return False

def do_something(dev):
	# print dev.AbortAssociation()
	# print dev.Connect()
	# print dev.RequestMeasurementDataTransmission()
	# print dev.RequestActivationScanner(55)
	# print dev.RequestDeactivationScanner(55)
	# print dev.ReleaseAssociation()
	# print dev.Disconnect()
	return False

# H&C
def parseDeviceXmlData(xmlData):
	parsedData = []

	try:
		xmlDoc = parseString(xmlData)
	except:
		return parsedData

	for simple in xmlDoc.getElementsByTagName("simple"):
		for name in simple.getElementsByTagName("name"):
			sname = getText(name).strip()
			if "Simple-Nu-Observed-Value" != sname and "Basic-Nu-Observed-Value" != sname:
				continue

			#print "Name: " + sname
			values = simple.getElementsByTagName("value")
			if values:
				value = getText(values[0]).strip()
				value = str(round(float(value), 2))
				parsedData.append(value)
				#print "Value: " + value
	
	for compound in xmlDoc.getElementsByTagName("compound"):
		for internalCompound in compound.getElementsByTagName("compound"):
			for name in internalCompound.getElementsByTagName("name"):
				sname = getText(name).strip()
				if "Compound-Basic-Nu-Observed-Value" != sname:
					continue
				#print "Name: " + sname
				for simple in internalCompound.getElementsByTagName("simple"):
					values = simple.getElementsByTagName("value")
					if values:
						value = getText(values[0]).strip()
						value = str(round(float(value), 2))
						parsedData.append(value)
						#print "Value: " + value
	return parsedData

def getText(node):
    rc = []
    for node in node.childNodes:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def createScaleXmlToPost(weight, bodyFat, skeletalMuscle):
	observationData = Element("ObservationData")

	deviceSerialNumber = SubElement(observationData, "DeviceSerialNumber").text = "OMRON_HBF-206IT"
	observationIdentifier = SubElement(observationData, "ObservationIdentifier").text = "MDC_DEV_SPEC_PROFILE_SCALE"
	observationDate = SubElement(observationData, "ObservationDate").text = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "+0100"

	observationMeasure1 = SubElement(observationData, "ObservationMeasure")
	observationDataType = SubElement(observationMeasure1, "ObservationDataType").text = "MDC_MASS_BODY_ACTUAL"
	observationValue = SubElement(observationMeasure1, "ObservationValue").text = weight
	
	observationMeasure2 = SubElement(observationData, "ObservationMeasure")
	observationDataType = SubElement(observationMeasure2, "ObservationDataType").text = "MDC_BODY_FAT_RATE"
	observationValue = SubElement(observationMeasure2, "ObservationValue").text = bodyFat

	observationMeasure3 = SubElement(observationData, "ObservationMeasure")
	observationDataType = SubElement(observationMeasure3, "ObservationDataType").text = "MDC_SKELETAL_MUSCLE_RATE"
	observationValue = SubElement(observationMeasure3, "ObservationValue").text = skeletalMuscle

	scaleXmlToPost = tostring(observationData)
	#print "ScaleXmlToPost: " + scaleXmlToPost
	
	return scaleXmlToPost

def createSphygmomanometerXmlToPost(sys, dia, pulse):
	observationData = Element("ObservationData")
	
	deviceSerialNumber = SubElement(observationData, "DeviceSerialNumber").text = "OMRON_HEM-7081-IT"
	observationIdentifier = SubElement(observationData, "ObservationIdentifier").text = "MDC_DEV_SPEC_PROFILE_BP"
	observationDate = SubElement(observationData, "ObservationDate").text = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "+0100"

	observationMeasure1 = SubElement(observationData, "ObservationMeasure")
	observationDataType = SubElement(observationMeasure1, "ObservationDataType").text = "MDC_PRESS_BLD_NONINV_SYS"
	observationValue = SubElement(observationMeasure1, "ObservationValue").text = sys

	observationMeasure2 = SubElement(observationData, "ObservationMeasure")
	observationDataType = SubElement(observationMeasure2, "ObservationDataType").text = "MDC_PRESS_BLD_NONINV_DIA"
	observationValue = SubElement(observationMeasure2, "ObservationValue").text = dia

	observationMeasure3 = SubElement(observationData, "ObservationMeasure")
	observationDataType = SubElement(observationMeasure3, "ObservationDataType").text = "MDC_PULS_RATE_NON_INV"
	observationValue = SubElement(observationMeasure3, "ObservationValue").text = pulse
	
	sphygmomanometerXmlToPost = tostring(observationData)
	#print "SphygmomanometerXmlToPost: " + sphygmomanometerXmlToPost
	
	return sphygmomanometerXmlToPost

def createPulseoxymeterXmlToPost(pulseOx, satO2):
	observationData = Element("ObservationData")
	
	deviceSerialNumber = SubElement(observationData, "DeviceSerialNumber").text = "NONIN_MEDICAL_INC_515676"
	observationIdentifier = SubElement(observationData, "ObservationIdentifier").text = "MDC_DEV_SPEC_PROFILE_PULS_OXIM"
	observationDate = SubElement(observationData, "ObservationDate").text = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "+0100"

	observationMeasure1 = SubElement(observationData, "ObservationMeasure")
	observationDataType = SubElement(observationMeasure1, "ObservationDataType").text = "MDC_PULS_OXIM_SAT_O2"
	observationValue = SubElement(observationMeasure1, "ObservationValue").text = satO2
	
	observationMeasure2 = SubElement(observationData, "ObservationMeasure")
	observationDataType = SubElement(observationMeasure2, "ObservationDataType").text = "MDC_PULS_OXIM_PULS_RATE"
	observationValue = SubElement(observationMeasure2, "ObservationValue").text = pulseOx

	pulseoxymeterXmlToPost = tostring(observationData)
	#print "PulseoxymeterXmlToPost: " + pulseoxymeterXmlToPost
	
	return pulseoxymeterXmlToPost

def updateVirtualizer(xmlDataToPost):
	
	try:
		headers = {"Content-Type": "text/plain"}
		print "HTTP POST request:"
		print xmlDataToPost
		print
		print "HTTP POST response:"
		print requests.post(virtualizerService, data = xmlDataToPost, headers = headers, timeout=4, proxies = NO_PROXY).text
	except:
		print 'Virtualizer update timeout FAILURE'



args = sys.argv[1:]

i = 0
while i < len(args):
	arg = args[i]

	if arg == '--mds':
		get_mds = 1
	elif arg == '--set-time':
		set_time = 1
	elif arg == "--interpret" or arg == "--interpret-xml":
		interpret_data = 1
	elif arg == '--prefix':
		dump_prefix = args[i + 1]
		i += 1
	elif arg == '--get-segment':
		get_segment = 1
		get_pmstore = 1
	elif arg == '--clear-segment':
		clear_segment = 1
		get_pmstore = 1
	elif arg == '--clear-all-segments':
		clear_segment = 2
		get_pmstore = 1
	elif arg == '--store' or arg == '--pmstore' or arg == '--pm-store':
		pmstore_handle = int(args[i + 1])
		get_pmstore = 1
		i += 1
	elif arg == '--instance' or arg == '--inst' or arg == '--segment' or \
				arg == '--pm-segment'  or arg == '--pmsegment':
		pmsegment_instance = int(args[i + 1])
		i += 1
	else:
		raise Exception("Invalid argument %s" % arg)

	i += 1
	

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

bus = dbus.SystemBus()

def bus_nameownerchanged(service, old, new):
	if service == "com.signove.health":
		if old == "" and new != "":
			start()
		elif old != "" and new == "":
			stop()

bus.add_signal_receiver(bus_nameownerchanged,
			"NameOwnerChanged",
			"org.freedesktop.DBus",
			"org.freedesktop.DBus",
			"/org/freedesktop/DBus")

def stop():
	global system_ids
	print "Detaching..."
	system_ids = {}

def start():
	#print "Starting..."
	try:
		obj = bus.get_object("com.signove.health", "/com/signove/health")
	except:
		print "Healthd service not found, waiting..."
		return
	srv = dbus.Interface(obj, "com.signove.health.manager")
	#print "Configuring..."
	srv.ConfigurePassive(agent, [0x1004, 0x1007, 0x1029, 0x100f])
	print "Waiting for a Continua device to connect..."

agent = Agent(bus, "/com/signove/health/agent/%d" % os.getpid())

start();

mainloop = glib.MainLoop()
mainloop.run()
