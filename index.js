var express = require("express");  
var app = express();  
var MongoClient = require("mongodb").MongoClient;  

app.get("/", function(req, res) {  
  res.send("Hello World!");  
});  

var DB_URL = "mongodb://10.192.20.114:27017/family"



MongoClient.connect(DB_URL,function(error,db){
	if (error) throw error;
  var dbo = db.db("family");
  dbo.collection("family").findOne({}, function(err, result) {
    if (err) throw err;
    console.log(result.name);
    db.close();
  });
});

app.listen(3000,function(){  
    console.log('Express app start on port 3000')  
});