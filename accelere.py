#!/usr/bin/python2.7

import os
import sys
import argparse
import urllib
import threading
import signal
import time
import Queue


class CleanErrorParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        sys.stderr.write('use -h or --help for usage information\n')
        #self.print_help()
        sys.exit(2)
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

if len(sys.argv)==1: #if we have no arguments:
    parser.print_help()
    sys.exit()





interrupted = False
done = False
def signal_handler(signum, frame):
    global interrupted
    print "\rInterrupted, waiting wayward threads.."
    interrupted = True
signal.signal(signal.SIGINT, signal_handler)

count = 0

# http://images.wsdot.wa.gov/nw/525vc00820.jpg
# http://140.160.161.198/axis-cgi/jpg/image.cgi?camera=1&resolution=460x345&compression=0

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

#check storage directory
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
settings_file = open(".accelere", "w")
settings_file.write(image_url)

print   "\nAccelere started\n" + \
        "  Image URL:\t"      + image_url + "\n" + \
        "  Max Images:\t"     + str(max_images) + "\n" + \
        "  Interval:\t"       + str(thread_interval) + "s\n" + \
        "  Storage Dir\t" + storage_dir + "\n"
# Queue to store our timestamps so we know how large to let the window get
# before we start deleting old images.
q = Queue.Queue(max_images)

def spawnDownloaderThread():
    thread = threading.Thread(target=downloadImage)
    #thread.daemon = True
    thread.start()
    return thread

# Grab an image from the desired URL and store it appropriately. Then manage
# the queue as necessary.
def downloadImage():
    global count
    timestamp = str(int(time.time()))
    count = count + 1
    print "Retrieving image " + str(count) + "..."

    # Download the image and save it.
    if args.dry != True:
    	urllib.urlretrieve(image_url, storage_dir + timestamp + image_type);
        print "Downloaded image " + str(count) + " to " + storage_dir + timestamp + image_type   
 
    # Check whether the queue is full. If so, remove the oldest timestamp.
    if q.full():
        os.remove(storage_dir + q.get() + image_type)

    # Add new image to the queue.
    q.put(timestamp)

# Run the program

# Cleanly exit by pressing q. Will wait on pending images.

while not interrupted:
    thread = spawnDownloaderThread() #this call will block if sigint has told us we are terminating
    if not interrupted: #I don't know how to make this part cleaner, we want to bail before the sleep
        time.sleep(thread_interval)
thread.join()
print "done."
