var bleacon = require('bleacon');
var noble = require('noble');
var config = require('./config');

var awsIot = require('aws-iot-device-sdk');

var Gpio = require('onoff').Gpio,

led = new Gpio(17, 'out');


//Setting IoT device parameters
var device = awsIot.device({
   keyPath: config.keyPath,
  certPath: config.certPath,
    caPath: config.caPath,
  clientId: config.clientId,
    region: config.region
});

var beacons = [];
led.writeSync(1);  // Turn LED on.

//console.log('Started Scanning........');
function Beacon_scanning(){
	noble.stopScanning();
	//console.log('Stop Scan...');
	clearInterval(interval); // Stop blinking
	//if(beacons.length > 0){
        publishToAWS(beacons);
	//}
	beacons.length = 0;
	console.log('New Scan...');

	var interval = setInterval(function(){
		led.writeSync(led.readSync() === 0 ? 1 : 0)
	}, 500);

    noble.startScanning([],false, function(error) {	
        if (error) {
            console.error('error', error);
            led.writeSync(0);  // Turn LED off.
            led.unexport();    // Unexport GPIO and free resources
        };
   	});
}

device.on('connect', function(){
	console.log("connected to AWS...");
	var interval = setInterval(Beacon_scanning, config.interval);
    noble.stopScanning();
});

bleacon.on('discover', function(bleBeacon) {
	//console.log('beacon found: ' + JSON.stringify(beacon));
	//device.publish('enbw_demo/BTGateways/Reply-JBox2/80:00:0B:40:E9:20', JSON.stringify(bleBeacon));
	addBeaconToList(bleBeacon);
});

function addBeaconToList(beacon){
	beacons.push(beacon);
	console.log('Added beacon: ', beacon.MAC_Address);
}

function publishToAWS(jsonString){
    console.log('Publish ' + jsonString.length + ' beacon/s to AWS IoT...');
    jsonString = '{"temperature": "' + '24' + '", "last scan": "' + new Date() + '", "beacons": ' + JSON.stringify(jsonString) + '}'
    console.log(jsonString);
	device.publish('enbw_demo/BTGateways/' + config.clientId + '/00:1A:7D:DA:71:0A', jsonString);
}

process.on('exit', function () {
  console.log('Keyboard interrupt');
  led.writeSync(0);  // Turn LED off.
  led.unexport();    // Unexport GPIO and free resources

})

//Bleacon.stopScanning();
