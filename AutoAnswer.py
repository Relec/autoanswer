import urllib2
import xml.etree.ElementTree as ET
import threading
import praw
import time
from multiprocessing.pool import ThreadPool


# Constants
footer = "\n***\n ^^This ^^answer ^^was ^^generated ^^by ^^a ^^bot."
header = ""
wolfram_key = "yourkey"

blacklist = []
pool = ThreadPool(processes=1)

# Login to Reddit
r = praw.Reddit('AutoAnswer Bot by u/_Heckraiser2_ v 1')
print("Logging in...")
r.login("ausername", "password")
print("Login success.")
print("Importing Ids...")

# Import IDs
with open('ids.txt', 'r') as f:
    already_done = [line.strip() for line in f]
print("Ids imported.")


# Write already commented comment id's to a text file.
def write_id(comment):
    with open("ids.txt", "a") as text_file:
        text_file.write(comment.id + "\n")
        text_file.close()


# Send the comment reply to reddit
def reply_to_comment(comment, text):
    comment.reply(header + text + footer)
    already_done.append(comment.id)


# Query WolframAlpha for the answer and return it
def query(q, key=wolfram_key):
    joined = ""
    ques = urllib2.urlopen('http://api.wolframalpha.com/v2/query?appid=%s&input=%s&format=plaintext' %
                           (key, urllib2.quote(q))).read()
    root = ET.fromstring(ques)
    for pt in root.findall('.//plaintext'):
        if pt.text:
            joined += pt.text
    return joined


def parse_comment(comment):
    if comment.id not in already_done:
        comment1 = comment.body.lower()
        if ":" in comment1:
            param, value = comment1.split(":", 1)
            value = value.strip()
            if not value == "":
                async_result = pool.apply_async(query, (value,))
                res = async_result.get()
                if res != "":
                    print value
                    print res
                    threading.Thread(target=reply_to_comment, args=(comment, res)).start()
                    threading.Thread(target=write_id, args=(comment,)).start()
                elif res == "":
                    print "No definition found."
                    failed = "Sorry I wasn't able to find an answer to that question. " \
                             "Try this google link instead: https://www.google.com/#q=" + value.replace(" ", "+")
                    threading.Thread(target=reply_to_comment, args=(comment, failed)).start()
                    threading.Thread(target=write_id, args=(comment,)).start()


# Main loop for comment searching
def main_loop():
    # Main loop start here...
    print("Starting...")
    while True:
        # Read the blacklist and place it into an array
        with open("blacklist.txt", 'r') as f:
            del blacklist[:]
            for entry in f.readlines():
                blacklist.append(entry.strip())

        # Start the comment loop
        try:
            # Grab as many comments as we can and loop through them
            for comment in r.get_comments("all", limit=None):
                # Check if the comment meets the basic criteria
                if "auto answer:" in comment.body.lower():
                    print("Comment found. Parsing...")
                    threading.Thread(target=parse_comment, args=(comment,)).start()

            # Finally wait 30 seconds
            print("Sleeping...")
            time.sleep(30)
            print("Starting..")
        except Exception as e:
            print(e)

# Threads!
main_thread = threading.Thread(target=main_loop)
# Start threads!
main_thread.start()