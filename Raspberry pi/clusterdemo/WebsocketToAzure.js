// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

'use strict';

var Amqp = require('azure-iot-device-amqp').Amqp;
// Uncomment one of these transports and then change it in fromConnectionString to test other transports
// var AmqpWs = require('azure-iot-device-amqp-ws').AmqpWs;
// var Http = require('azure-iot-device-http').Http;
// var Mqtt = require('azure-iot-device-mqtt').Mqtt;
var Client = require('azure-iot-device').Client;
var Message = require('azure-iot-device').Message;

var hostname = 'TelemedizinIotHub.azure-devices.net';
var deviceid = 'RaspberryPi';
var sharedaccesskey = '/691KueWIjA2wAVHRAiQgGapn1mmarMgc8zYvEUWE6g=';

var ws = require('nodejs-websocket')

// String containing Hostname, Device Id & Device Key in the following formats:
//  "HostName=<iothub_host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>"
var connectionString = 'HostName=TelemedizinIotHub.azure-devices.net;DeviceId=RaspberryPi;SharedAccessKey=/691KueWIjA2wAVHRAiQgGapn1mmarMgc8zYvEUWE6g=';

// fromConnectionString must specify a transport constructor, coming from any transport package.
var client = Client.fromConnectionString(connectionString, Amqp);

var connectCallback = function(err) {
    if(err) {
        console.log('Could not connect: ' + err.message);
    } else {
        console.log('            ***Azure-Client connected***');
	console.log('');
	console.log('Host Name: ' + hostname);
	console.log('Device Id: ' + deviceid);
	console.log('Shared Access Key: ' + sharedaccesskey);
	console.log('')
        client.on('message', function (msg) {
            console.log('Id: ' + msg.messageId + ' Body: ' + msg.data);
            client.complete(msg, printResultFor('completed'));
            // reject and abandon follow the same pattern.
            // /!\ reject and abandon are not available with MQTT
        });
        
        // Create a message and send it to the IoT Hub every second
        // var sendInterval = setInterval(function () {
        //     var windSpeed = 10 + (Math.random() * 4); // range: [10, 14]
        //     var data = JSON.stringify({ deviceId: 'myFirstDevice', windSpeed: windSpeed });
        //     var message = new Message(data);
        //     message.properties.add('myproperty', 'myvalue');
        //     console.log('Sending message: ' + message.getData());
        //     client.sendEvent(message, printResultFor('send'));
        // }, 2000);
        
        client.on('error', function (err) {
            console.log(err.message);
        });

        client.on('disconnect', function(){
            // clearInterval(sendInterval);
            client.removeAllListeners();
            client.connect(connectCallback);
        });
    }
};

client.open(connectCallback);

// Helper function to print results in the console
function printResultFor(op) {
  return function printResult(err, res) {
    if (err) console.log(op + ' error: ' + err.toString());
    if (res) console.log(op + ' status: ' + res.constructor.name);
  };
}

//WS Server
var server = ws.createServer(function (conn) {
	console.log("        ***Health Device Client connected***")
	console.log(" ");
	conn.on("text", function (str) {
		console.log("                  ***Received message***");
		console.log(str);
        	var message = new Message(str);
        	message.properties.add('myproperty', 'myvalue');
        	console.log('Sending message to Azure IoT Hub: ' + message.getData());
        	client.sendEvent(message, printResultFor('send'));
		conn.sendText("success!")
	})
	conn.on("close", function (code, reason) {
		console.log("              ***Connection closed***")
	})
}).listen(8001)
