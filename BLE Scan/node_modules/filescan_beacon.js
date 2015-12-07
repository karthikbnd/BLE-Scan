var Bleacon = require('bleacon');
//var uuid = '047a40bc4d4d4dba913f0656df1171e3';
//Bleacon.startScanning([uuid], [major], [minor]);// scan for bleacons with a particular uuid. major, and minor
Bleacon.startScanning(); // scan for any bleacons
console.log('Started Scanning........');
Bleacon.on('discover', function(bleacon) {
	console.log('beacon found: ' + JSON.stringify(bleacon));
});

Bleacon.stopScanning();
