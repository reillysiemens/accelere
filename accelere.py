#!/usr/bin/python2.7

import os, sys, urllib, threading, signal, time, Queue

exit = False

def signal_handler(signal, frame):
    global exit
    exit = True

signal.signal(signal.SIGINT, signal_handler) #expanding this will allow clean exits (no half images)


def timerControl():
    if exit:
        return
    threading.Timer(10.0, lambda: timerControl()).start()
    getpic()
    print 'getting picture...'

q = Queue.Queue(5)

def getpic():
    timestamp = str(int(time.time()))
    urllib.urlretrieve("http://images.wsdot.wa.gov/nw/525vc00820.jpg", timestamp + ".jpg");
    
    # check if queue is full remove oldest if it is
    if q.full():
        os.remove(q.get() + ".jpg")

    # add new image to the queue
    q.put(timestamp)

timerControl()

while True:
    a = raw_input()
    if a == 'a':
        break;
exit = True
