#!/usr/bin/python2.7

import os
import sys
import urllib
import threading
import signal
import time
import Queue

exit = False

count = 1
max_images = 1440
thread_interval = 5.0
image_url = "http://images.wsdot.wa.gov/nw/525vc00820.jpg"
image_type = ".jpg"
storage_dir = "./storage/"

# Queue to store our timestamps so we know how large to let the window get
# before we start deleting old images.
q = Queue.Queue(max_images)

def signal_handler(signal, frame):
    global exit
    exit = True

# Expanding this will allow clean exits (no half images).
signal.signal(signal.SIGINT, signal_handler) 

# Spawns a new thread every 60 seconds to run the getpic() function.
def timerControl():
    if exit:
        return
    threading.Timer(thread_interval, lambda: timerControl()).start()
    getpic()

# Grab an image from the desired URL and store it appropriately. Then manage
# the queue as necessary.
def getpic():
    global count
    timestamp = str(int(time.time()))

    print "Retrieving image " + str(count) + "..."
    count = count + 1

    # Download the image and save it.
    urllib.urlretrieve(image_url, storage_dir + timestamp + image_type);
    
    # Check whether the queue is full. If so, remove the oldest timestamp.
    if q.full():
        os.remove(storage_dir + q.get() + image_type)

    # Add new image to the queue.
    q.put(timestamp)

# Run the program
timerControl()

# Cleanly exit by pressing q. Will wait on pending images.
while True:
    a = raw_input()
    if a == 'q':
        break;

exit = True
