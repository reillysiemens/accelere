#!/usr/bin/python2.7

import os
import sys
import argparse
import urllib
import threading
import signal
import time
import Queue

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--max", type=int, help="the maximum number of images to keep")
parser.add_argument("-i", "--interval", type=float, help="the interval between threads")
parser.add_argument("-t", "--type", help="the type of image to create")
parser.add_argument("-l", "--location", help="the location from which to retrieve images")
parser.add_argument("-d", "--directory", help="the storage directory location")
parser.add_argument("--dev", help="the program runs in development mode")
args = parser.parse_args()

exit = False

count = 1

if args.dev == "true":
    max_images = 1440
    thread_interval = 5.0
    image_type = ".jpg"
    image_url = "http://images.wsdot.wa.gov/nw/525vc00820.jpg"
    storage_dir = "./storage/"
else:
    max_images = args.max
    thread_interval = args.interval
    image_type = args.type
    image_url = args.location
    storage_dir = args.directory

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
