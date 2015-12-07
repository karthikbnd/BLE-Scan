var noble = require('noble');
console.log('called noble');
var allowDuplicates = false; //To allow duplicates: 1 or true //Not to allow duplicates: 0 or false

//noble.startScanning();
noble.on('stateChange', function(state) {
  if (state === 'poweredOn') {
    noble.startScanning([],allowDuplicates, function(error) {		
      if (error) {
        console.log('error ', error);
      };
     console.log('started scanning.\ncurrent state:', state);
    });
  } else {
    console.log('stopped scanning. current state: ', state);
    process.exit();
    noble.stopScanning();
  }
});

noble.on('discover', function(peripheral) {
  var id = peripheral.id; 
  var macAddress = peripheral.uuid; 
  var rssi = peripheral.rssi;
  var localName = peripheral.advertisement.localName;
  var address = peripheral.address;
  var type = peripheral.addressType; 
  var date = new Date();
  var distance = calculateDistance(rssi);
  console.log('Found BLE:', 'MAC Address:',address, ' RSSI:',rssi,'BLE Name:',localName, 'Distance:', distance, 'Date:',date, 'Type:',type );   
});

function calculateDistance(rssi) {
  
  var txPower = -59 //hard coded power value. Usually ranges between -59 to -65
  
  if (rssi == 0) {
    return -1.0; 
  }

  var ratio = rssi*1.0/txPower;
  if (ratio < 1.0) {
    return Math.pow(ratio,10);
  }
  else {
    var distance =  (0.89976)*Math.pow(ratio,7.7095) + 0.111;    
    return distance;
  }
} 
