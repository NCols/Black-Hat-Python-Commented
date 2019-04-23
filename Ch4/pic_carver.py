#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
We will attempt to carve out image files from HTTP traffic.
With these image files in hand,we will use OpenCV2, a computer
vision tool, to attempt to detect images that contain human
faces so that we can narrow down images that might be interesting.
We can use our previous ARP poisoning script to generate
the PCAP files or you could extend the ARP poisoning sniffer to do on-the-
fly facial detection of images while the target is browsing.

NB: During my tests I couldn't get the facial recognition to work, but the HTTP
scraping part seems to be working fine.
"""

import re
import zlib
import cv2
from scapy.all import *

pictures_directory = "./pic_carver/pictures"
faces_directory = "./pic_carver/faces"
pcap_file = "test-images.pcap"

# These are the supporting functions that allow http_assembler() to work
def get_http_headers(http_payload):
    try:
        # Split the headers off if it is HTTP traffic
        headers_raw = http_payload[:http_payload.index("\r\n\r\n")+2]
        # Break out the headers
        headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", headers_raw))
    except:
        return None

    return headers

def extract_image(headers,http_payload):
    image = None
    image_type = None

    try:
        print("Header: ")
        print(headers)
        # If we detect that the Content-Type header does indeed contain the image MIME type
        if "image" in headers['Content-type']:
            # Grab the image type and image body
            image_type = headers['Content-type'].split("/")[1]
            image = http_payload[http_payload.index("\r\n\r\n")+4:]
            # print("Image type: ",image_type)
            # print("Image: ",image)
            # If we detect compression, decompress the image
            try:
                if "Content-Encoding" in headers.keys():
                    if header["Content-Encoding"] == "gzip":
                        image = zlib.decompress(image, 16+zlib.MAX_WBITS)
                    elif headers["Content-Encoding"] == "deflate":
                        image = zlib.decompress(image)
            except:
                pass

    except:
        print("Error in detecting image.")
        print("**********************************")
        return None,None

    print("**********************************")
    return image,image_type


# Facial detection code
# This code was generously shared by Chris Fidao at http://www.fideloper.com/facial-detection/
# and slightly modified for the 'Black Hat Python' book
def face_detect(path, file_name):
    # Read the image
    img = cv2.imread(path)
    # Apply a classifier that is trained in advance for detecing faces in a front-facing orientation
    # There are other classifiers (profile, hands, fruits etc) that we can try out for ourselves
    cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")
    rects = cascade.detectMultiScale(img,1.3,4,cv2.cv.CV_HAAR_SCALE_IMAGE, (20,20))

    if len(rects) == 0:
        return False

    rects[:, 2:] += rects[:,:2]

    # Highlight the faces in the image
    # After detection has been run, it will return rectangle
    # coordinates that correspond to where the face was detected in the image.
    # We then draw an actual green rectangle over that area and write out the resulting image.
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img,(x1,y1),(x2,y2),(127,255,0),2)

    cv2.imwrite("%s/%s-%s" % (faces_directory, pcap_file, file_name), img)

    return True

# This is the main function
def http_assembler(pcap_file):
    carved_images = 0
    faces_detected = 0

    # We start by opening a pcap file for processing
    a = rdpcap(pcap_file)

    # Separate each TCP session into a dictionary
    sessions = a.sessions()
    for session in sessions:
        http_payload = ""
        for packet in sessions[session]:
            try:
                # We isolate HTTP traffic and concatenate the payload of all the traffic into a single buffer
                # Similar to "Follow TCP Stream" in Wireshark
                if packet[TCP].dport == 8000 or packet[TCP].sport == 8000:
                    # Reassemble the stream
                    http_payload += str(packet[TCP].payload)
            except:
                pass
        # HTTP header parsing function, allows us to inspect HTTP headers individually
        headers = get_http_headers(http_payload)
        if headers is None:
            continue

        # After we validate that we are receiving an image back in an HTTP response,
        # we extract the raw image and return the image type and the binary body of
        # the image itself.
        image, image_type = extract_image(headers,http_payload)

        if image is not None and image_type is not None:
            # Store the image
            file_name = "%s-pic_carver_%d.%s" % (pcap_file,carved_images,image_type)
            fd = open("%s%s" % (pictures_directory,file_name),"wb")
            fd.write(image)
            fd.close()

            carved_images += 1

            # Now attempt face recognition
            try:
                result = face_detect("%s%s" % (pictures_directory,file_name),file_name)
                if result is True:
                    faces_detected += 1
            except:
                pass
    return carved_images, faces_detected

carved_images, faces_detected = http_assembler(pcap_file)

print("Extracted: %d images" % carved_images)
print("Detected: %d faces" % faces_detected)
