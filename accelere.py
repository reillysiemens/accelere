#!/usr/bin/python2.7

import os
import sys
import argparse
import urllib
import threading
import signal
import time
import Queue

#Override the error def on argparse.ArgumentParser
#to display specific information on error
class CleanErrorParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        sys.stderr.write('use -h or --help for usage information\n')
        #self.print_help()
        sys.exit(2)

#Create, configure, and run the parser
parser = CleanErrorParser()
parser.add_argument("-m", "--max", 	        type=int, 	help="the maximum number of images to keep",        default=1024)
parser.add_argument("-i", "--interval",     type=float, help="the interval between threads",                default=60.0)
parser.add_argument("-t", "--type", 			        help="the type of image to create",                 default=".jpg")
parser.add_argument("-l", "--location",			        help="the location from which to retrieve images",  default="")
parser.add_argument("-L", "--lastlocation",             help="use last location (stored in .accelere)",     action="store_true")
parser.add_argument("-d", "--directory", 		        help="the storage directory location",              default="./storage/")
parser.add_argument("--dev", 				            help="the program runs in development mode",        action="store_true")
parser.add_argument("--dry", 				            help="does not acquire images, only shows debug",   action="store_true")
args = parser.parse_args()

#error handling for no arguments (accelere.py is 1 argument)
if len(sys.argv)==1: #if we have no arguments:
    parser.print_help()
    sys.exit()

#bool interrupted becomes true if sigint is received
interrupted = False

#handle sigints by setting interrupted to true
def signal_interrupt_handler(signum, frame):
    global interrupted
    print "\rInterrupted, waiting for wayward threads.."
    interrupted = True

#define handler function for sigints to be signal_interrupt_handler
signal.signal(signal.SIGINT, signal_interrupt_handler)

#Tracks the number of images download attempts
image_download_count = 0

# http://images.wsdot.wa.gov/nw/525vc00820.jpg
# http://140.160.161.198/axis-cgi/jpg/image.cgi?camera=1&resolution=460x345&compression=0

#TODO: comment this better? clean this up?
#Checks if dev is true and sets required variables
if args.dev == True:
    max_images = 28800
    thread_interval = 3.0
    image_type = ".jpg"
    image_url = "http://140.160.161.198/axis-cgi/jpg/image.cgi?camera=1&resolution=460x345&compression=0"
    storage_dir = "./storage/"
else:
    max_images = args.max
    thread_interval = args.interval
    image_type = args.type
    image_url = args.location
    storage_dir = args.directory

#check storage directory and attempts to create if it does not exist
#exits if there is an error creating the directory
if not os.path.isdir(storage_dir):
    print "Directory " + storage_dir + " does not exist, attempting to create..."
    try:
        os.makedirs(storage_dir)
    except:
        print "Directory creation failed!"
        os.exit()

#Read from last location file if we are going to use it
if args.lastlocation == True:
    try:
        settings_file = open(".accelere", "r")
        image_url = settings_file.read()
        settings_file.close()
    except:
    #fail gracefully (should probably fail more gracefully than this
	print "error with last location, please specify location with -l"
	sys.exit()

#save location to the settings file
try:
    settings_file = open(".accelere", "w")
    settings_file.write(image_url)
    settings_file.close()
except:
    print "Error saving location to settings file (does someone else have a lock?)"

#Prints variable output before accelere starts
print   "\nAccelere started\n" + \
        "  Image URL:\t"      + image_url + "\n" + \
        "  Max Images:\t"     + str(max_images) + "\n" + \
        "  Interval:\t"       + str(thread_interval) + "s\n" + \
        "  Storage Dir\t" + storage_dir + "\n"

# Queue to store our timestamps so we know how large to let the window get
# before we start deleting old images.
q = Queue.Queue(max_images)

#Creates the downloader thread using the downloadImage function
#Starts the thread and returns a reference to it
def spawnDownloaderThread():
    thread = threading.Thread(target=downloadImage)
    #thread.daemon = True
    thread.start()
    return thread

# Grab an image from the desired URL and store it appropriately. Then manage
# the queue as necessary.
def downloadImage():
    global image_download_count
    timestamp = str(int(time.time()))
    image_download_count = image_download_count + 1
    print "Retrieving image " + str(image_download_count) + "..."

    # Download the image and save it.
    if args.dry != True:
    	urllib.urlretrieve(image_url, storage_dir + timestamp + image_type);
        print "Downloaded image " + str(image_download_count) + " to " + storage_dir + timestamp + image_type   
 
    # Check whether the queue is full. If so, remove the oldest timestamp.
    if q.full():
        os.remove(storage_dir + q.get() + image_type)

    # Add new image to the queue.
    q.put(timestamp)

# Run the program
# Cleanly exit by pressing ctrl-c. Will wait on pending images.

while not interrupted:
    thread = spawnDownloaderThread() #this call will block if sigint has told us we are terminating
    if not interrupted: #I don't know how to make this part cleaner, we want to bail before the sleep
        time.sleep(thread_interval)

#wait on last thread (this could potentially cut off image downloads that remain unfinished
#if they began before the most recent thread, could use a pool to handle this I think? but not
#sure if that should matter because the resource would not even be available if a new image has
#been stored (is this even how webservers work if a download is in progress and the resource changes?)
thread.join()
print "Done."
