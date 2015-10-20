"""Nasa Epic Image fetcher."""
__author__ = "Walter A. Boring IV"
import argparse
import requests
import os
from StringIO import StringIO
from PIL import Image
import pprint
import sys
import json
import errno

parser = argparse.ArgumentParser()
parser.add_argument("-debug", help="Turn on client http debugging",
                    default=False, action="store_true")
args = parser.parse_args()


class NasaEpic(object):
    """Fetch the images from the Nasa Epic website.
       Based on
        http://epic.gsfc.nasa.gov/

        http://epic.gsfc.nasa.gov/api/images.php?date=2015-10-16
    """

    base_url = "http://epic.gsfc.nasa.gov/api/images.php?"
    image_url = "http://epic.gsfc.nasa.gov/epic-archive/png/"

    def __init__(self, debug):
        self.debug = debug

    def getValidDates(self):
        print("Fetching valid dates")
        date_url = "http://epic.gsfc.nasa.gov/api/images.php?dates"
        r = requests.get(date_url)
        date_str = ""
        
        dates = r.content.replace("var enabledDates = ","")
        dates = dates.replace(";", "")
        dates = json.loads(dates)
	print("found %s valid dates" % len(dates))
        return dates

    def createFilename(self, url, name, folder):
        return folder + "/" + name

    def getImageFast(self, url, name=None, folder='./'):
        print("downloading image %s" % name)
        file = self.createFilename(url, name, folder)
        r = requests.get(url)
        i = Image.open(StringIO(r.content))
        i.save(file)

    def getImageProgress(self, url, name, folder):
        file = self.createFilename(url, name, folder)
        r = requests.get(url, stream=True)
        total_length = r.headers.get('content-length')

        if total_length is None: # no content length header
            with open(file, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        else:
            with open(file, 'wb') as f:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content():
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )    
                    sys.stdout.flush()

    def ensureDir(self, dir):
        try:
            os.makedirs(dir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        
        return os.path.realpath(dir)

    def fetchDate(self, date, dir):
        print("Finding images for date %s" % date)
        url = self.base_url + "date=%s" % date
        r = requests.get(url)
        #print("JSON = %s" % r.json())
        image_data = r.json()
        print("Found %s images for %s" % (len(image_data), date))
        for image in image_data:
            image_name = image['image'] + '.png'
            full_path = os.path.realpath(dir + "/" + image_name)
            if not os.path.exists(full_path):
                image_url = self.image_url + image_name
                #self.getImageFast(image_url, name=image_name, folder=dir)
                self.getImageProgress(image_url, name=image_name, folder=dir)
            else:
                print("%s already exists" % image_name)

    def run(self):
        dates = self.getValidDates()
        for date in dates:
            dir = self.ensureDir("./%s" % date)
            #print("DIR = %s" % dir)
            self.fetchDate(date, dir)
        


def main():
    NasaEpic(args.debug).run()


if __name__ == '__main__':
    main()
