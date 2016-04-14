var Bleacon = require('bleacon');
//var uuid = '047a40bc4d4d4dba913f0656df1171e3';
//Bleacon.startScanning([uuid], [major], [minor]);// scan for bleacons with a particular uuid. major, and minor
Bleacon.startScanning(); // scan for any bleacons
console.log('Started Scanning........');
Bleacon.on('discover', function(bleacon) {
	console.log('beacon found: ' + JSON.stringify(bleacon));
});

Bleacon.stopScanning();


//Another file

var Bleacon = require('bleacon');
var noble = require('noble');
var interval = setInterval(Beacon_scanning, 10000);
function Beacon_scanning(){
Bleacon.startScanning();
}

Bleacon.on('discover', function(bleacon){
        //var obj = (bleacon);
        //return obj;
        if(bleacon.MAC_Address == "c6:3b:45:94:28:7d")console.log(JSON.stringify(bleacon));
        //console.log(bleacon);
});

//Bleacon.stopScanning();

