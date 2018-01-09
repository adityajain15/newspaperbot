const twit = require('twit');
const moment = require('moment');
const request = require('request');
const download = require('download-file')
const fs = require('fs');
const CronJob = require('cron').CronJob;

const config = require ('./config');

const Twitter = new twit(config);
const numMilSeconds = 1000*60*60*24;
const workingHours = 1000*60*60*12;
const baseUrl = `https://chroniclingamerica.loc.gov`;

/*
Twitter.post('statuses/update', { status: 'Hello world!' }, function(err, data, response) {
  console.log(data);
  console.log(`Response is ${response}`);
})*/

const job = new CronJob('00 00 04 * * *', function() {
  const today = moment().subtract(100, 'years').format('YYYY-MM-DD');
  const queryUrl = `${baseUrl}/frontpages/${today}.json`;
  
  request(queryUrl, function (error, response, body) {
    if(error) throw error
    
    const resp = JSON.parse(body);
    console.log('Recieved today\'s data');

    tweetNewspaper(resp,0);
  });
});

job.start();

function tweetNewspaper(resp,i,prevData){
  if(i>=resp.length) return

  const todayHuman = moment().subtract(100, 'years').format('MMMM Do YYYY');
  let options = {
      directory: "./assets/",
      filename: `${i}.jpg`
  }

  setTimeout(function(options,index){
    console.log(`Initiating download for URL: ${baseUrl}${resp[i].medium_url}`);

    download(`${baseUrl}${resp[i].medium_url}`, options, function(err){
      if (err) {
        console.log(`----------------Did not print ${i}-----------------`);
        tweetNewspaper(resp,i+1,prevData);      
      }

      console.log(`Downloaded image ${i}`);

      let b64content = fs.readFileSync(`./assets/${i}.jpg`, { encoding: 'base64' })
      Twitter.post('media/upload', { media_data: b64content }, function (err, data, response) {
        let mediaIdStr = data.media_id_string
        let altText = `Front page of the ${resp[i].label} dated ${todayHuman}`;
        let meta_params = {media_id: mediaIdStr, alt_text: {text: altText}};
        Twitter.post('media/metadata/create', meta_params, function (err, data, response) {
          if (!err) {

            let params = getParams(resp,prevData,i,mediaIdStr);

            Twitter.post('statuses/update', params, function (err, data, response) {
              console.log(data);
              tweetNewspaper(resp,i+1,data);
            })
          }        
        })
      })
    })
  },5000*i,options,i)
}

function getParams(resp,data,i,mediaIdStr){
  if(data!=undefined){
    return { 
      in_reply_to_status_id: data.id_str,
      status: `@${data.user.screen_name} (${i+1}/${resp.length}) On this day, 100 years ago

The front page of '${resp[i].label}'
Place of publication: ${resp[i].place_of_publication}

Read the high-resolution version here: ${baseUrl}${resp[i].url}`, 
      media_ids: [mediaIdStr] 
    }
  }
  else{
    return {
      status: `(${i+1}/${resp.length}) On this day, 100 years ago

The front page of '${resp[i].label}' 
Place of publication: ${resp[i].place_of_publication}

Read the high-resolution version here: ${baseUrl}${resp[i].url}`, 
      media_ids: [mediaIdStr] 
    }
  }
}