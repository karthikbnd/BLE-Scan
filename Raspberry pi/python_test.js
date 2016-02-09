var PythonShell = require('python-shell');

var options = {
  mode: 'text',
};

PythonShell.run('dht.py', options, function (err, results) {
  if (err) throw err;
  // results is an array consisting of messages collected during execution
  console.log('results: %j', results);
});