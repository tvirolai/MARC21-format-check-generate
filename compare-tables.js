/* jshint node: true */

"use strict";

const fs = require("fs");
const _ = require("underscore");
const out = fs.createWriteStream("comparison.log");

function readAFile(filename) {
  return new Promise( (resolve, reject) => {
    fs.readFile(filename, "utf-8", (err, data) => {
      if (err) reject(err);
      else  resolve(data);
    });
  });
}

function processData(data) {
  data = _.filter(data.split("\n"), line => Number(line.substring(0, 3)) > 0);
  data = _.map(data, line => {
    let keyValuePair = [];
    keyValuePair.push(line.substring(0,3));
    keyValuePair.push(line);
    return keyValuePair;
  });
  return _.object(data);
}

function sortKeys(data) {
  return Object.keys(data).sort();
}

function trimArray(array) {
  return _.filter(_.map(array, item => item.trim()), item => item.length > 0);
}

function compareLines(array1, array2, warnings, callback) {
  let item = array1.shift();
  let matchFound = false;
  for (let i = 0; i < array2.length; i++) {
    if (item.substr(0,2) === array2[i].substr(0, 2)) {
      if (item !== array2[i]) {
        warnings += "Subfield / item different: original: " + item + ", new: " + array2[i] + "\n";
      }
      matchFound = true;
    }
  }
  if (matchFound === false) {
    warnings += "Subfield missing from output: " + item + "\n";
  }
  if (array1.length > 0) {
    compareLines(array1, array2, warnings, callback);
  } else if (warnings.length > 5) {
    out.write(warnings + "\n");
    callback(warnings);
  }
}

var promises = ["./data/ma_bibl.chk_ORIG", "./data/ma_bibl.chk_NEW"].map(readAFile);

Promise.all(promises).then( data => {
  let oldData = processData(data[0]);
  let newData = processData(data[1]);
  _.each(sortKeys(oldData), key => {
    let oldItems = trimArray(oldData[key].split("|"));
    try {
      let newItems = trimArray(newData[key].split("|"));
      let warnings = key + ":\n";
      compareLines(oldItems, newItems, warnings, console.log);
    } catch (e) {
      out.write(key + ":\nField is missing from output.\n");
    }
  });
});
