var config = {};

config.keyPath = '/home/reply/certs/private.pem.key';
config.certPath = '/home/reply/certs/certificate.pem.crt';
config.caPath = '/home/reply/certs/root-CA.crt';
config.clientId = 'RaspberryPI-2-Cluster';
config.region = 'eu-west-1';

config.interval=10000;

module.exports = config;
