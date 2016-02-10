//var earthR = 6371;
//here the Lat and Lon are the latitudes and longitudes coordinates
//Reference Node 1
var LatA = 700;                 //x1
var LonA = 1100;                        //y1
var DistA = 0.265710701754;             //d1
//Reference Node 2
var LatB = 1600;                                //x2
var LonB = 500;                         //y2
var DistB = 0.26576;                    //d2
//Reference Node 3
var LatC = 2200;                                        //x3
var LonC = 1400;                                        //y3
var DistC = 0.0548954278262;                    //d2

var Radians = Math.PI/180;
var Degrees = 180/Math.PI;

var A = (Math.pow(LatA,2))+(Math.pow(LonA,2))-(Math.pow(DistA,2));
var B = (Math.pow(LatB,2))+(Math.pow(LonB,2))-(Math.pow(DistB,2));
var C = (Math.pow(LatC,2))+(Math.pow(LonC,2))-(Math.pow(DistC,2));

var X32 = LatC-LatB;
var X13 = LatA-LatC;
var X21 = LatB-LatA;

var Y32 = LonC-LonB;
var Y13 = LonA-LonC;
var Y21 = LonB-LonA;

var lat = ((A*Y32)+(B*Y13)+(C*Y21))/(2*((LatA*Y32)+(LatB*Y13)+(LatC*Y21)));             //Target node latitude
var lon = ((A*X32)+(B*X13)+(C*X21))/(2*((LonA*X32)+(LonB*X13)+(LonC*X21)));             //Target node longitude

console.log('Latitude:',lat);
console.log('Longitude:',lon);
