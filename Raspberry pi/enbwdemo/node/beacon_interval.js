var Bleacon = require('bleacon');
var noble = require('noble');
//var SysLogger = require('ain2');
//var console = new SysLogger();

var interval = setInterval(Beacon_scanning, 10000);
console.info('Started Scanning........');
function Beacon_scanning(){
Bleacon.startScanning();
}


Bleacon.on('discover', function(bleacon){
	console.log('beacon found: ' + JSON.stringify(bleacon));
});

Bleacon.stopScanning();
