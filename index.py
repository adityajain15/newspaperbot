import twitter
import arrow
import requests
import threading
import math
import shutil
import time
import random
import schedule

requests.get('https://api.github.com/events')

twtr = twitter.Api(
  consumer_key='consumer_key',
  consumer_secret='consumer_secret',
  access_token_key='access_token_key',
  access_token_secret='access_token_secret')

base_url = 'https://chroniclingamerica.loc.gov'

def worker(chunk,thread_num,num_partitions,date):
  for i in range(0,len(chunk)):
    img_resp = requests.get("%s%s"%(base_url,chunk[i]['medium_url']), stream=True)
    if img_resp.status_code == 200:
      with open("assets/%s.jpg"%((thread_num*num_partitions)+i), 'wb') as out_file:
        shutil.copyfileobj(img_resp.raw, out_file)
        print("%s Downloaded image %d"%(date,(thread_num*num_partitions)+i))
    if img_resp.status_code == 503:
      print('\x1b[1;37;41m'+" %s ERROR: Could not download image %d "%(date,(thread_num*num_partitions)+i)+ '\x1b[0m')

def startTweetin(data,num_tweets,today_date):
  prevTweet = None
  prevData = None
  sucess = 0
  for i in range(0,num_tweets):
    if(prevTweet):
      status = "@%s (%d/%d) On this day, 100 years ago\n\nThe front page of '%s'\nPlace of publication: %s\n\nRead the high-resolution version here: %s%s"%(prevData.user.screen_name,i+1,num_tweets,data[i]['label'],data[i]['place_of_publication'],base_url,data[i]['url'])
    else:
      status = "(%d/%d) On this day, 100 years ago\n\nThe front page of '%s'\nPlace of publication: %s\n\nRead the high-resolution version here: %s%s"%(i+1,num_tweets,data[i]['label'],data[i]['place_of_publication'],base_url,data[i]['url'])

    try:
      prevData = twtr.PostMedia(status,"assets/%d.jpg"%(i), possibly_sensitive=None, in_reply_to_status_id=prevTweet, latitude=None, longitude=None, place_id=None, display_coordinates=False)
      prevTweet = prevData.id
      print('\x1b[6;30;42m'+" %s Tweeted image %d "%(today_date,i)+ '\x1b[0m')
      sucess+=1
    except twitter.error.TwitterError as theError:
      print('\x1b[1;37;41m'+"%s"%(theError.args)+ '\x1b[0m')
      print('\x1b[1;37;41m'+" %s ERROR: Could not tweet image %d "%(today_date,i)+ '\x1b[0m')
    time.sleep(8)
  print('\x1b[1;37;44m'+" SUCCESS RATE: %d%% ( %d / %d ) " % (((sucess/num_tweets)*100),sucess,num_tweets)+ '\x1b[0m')
  return schedule.CancelJob

def getPictures():
  today_date = arrow.now().shift(years=-100).shift(days=+1).format('YYYY-MM-DD')
  r = requests.get("%s/frontpages/%s.json" % (base_url,today_date))
  r_json = r.json()
  num_partitions = math.ceil(len(r_json)/8)
  chunks = [r_json[x:x+num_partitions] for x in range(0, len(r_json), num_partitions)]
  threads = []
  for i in range(0,8):
    t = threading.Thread(target=worker, args=(chunks[i],i,num_partitions,today_date,))
    threads.append(t)
    t.start()
  for i in range(0,8):
    threads[i].join()
  schedule.every().day.at("04:00").do(startTweetin,r_json,len(r_json),today_date)

schedule.every().day.at("22:00").do(getPictures)

while 1:
    schedule.run_pending()
    time.sleep(1)