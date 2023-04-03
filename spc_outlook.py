#!/usr/bin/python3

import argparse
import datetime
import matplotlib.pyplot as pyplot
import matplotlib.path as mplpath
from matplotlib.patches import Polygon
import numpy
import requests
import requests.packages.urllib3.util.connection as urllib3_cn
import socket

def pad_date(dt):
    return str(dt.year) + str(dt.month).zfill(2) + str(dt.day).zfill(2)

def construct_url(dt):
    base_url = 'https://www.spc.noaa.gov/products/outlook/archive/{}/day1otlk_{}_{}_cat.lyr.geojson'
    if dt.hour == 0:
        dt -= datetime.timedelta(days=1)
        return base_url.format(dt.year, pad_date(dt), '2000');
    valid = [
        ('0100', 1, 0),
        ('1200', 12, 0),
        ('1300', 13, 0),
        ('1630', 16, 30),
        ('2000', 20, 0)
    ]
    timestamp = '0100'
    for v in valid:
        if dt.hour >= v[1] and dt.minute >= v[2]:
            timestamp = v[0]
    return base_url.format(dt.year, pad_date(dt), timestamp)

def parse_geojson(j, mycoords, graph):
    polygons = numpy.array([])
    for feature in j['features']:
        for riskarea in feature['geometry']['coordinates']:
            #TODO: I don't think this necessarily how multipolygons work, this might
            # give incorrect results in some situations.
            for ra in riskarea:
                polygons = numpy.append(
                    polygons,
                    {
                        'risk': feature['properties']['LABEL2'],
                        'polygon': Polygon(
                            numpy.array(ra),
                            edgecolor=feature['properties']['stroke'],
                            facecolor=feature['properties']['fill']
                        )
                    }
                )

    message = 'No severe weather risk'
    # This should already be in order from mrgl to high
    for polygon in polygons:
        path = mplpath.Path(polygon['polygon'].get_xy())
        if path.contains_point(mycoords):
            message = polygon['risk']
    print(message)

    if graph:
        figure,axes = pyplot.subplots()
        for polygon in polygons:
            axes.add_patch(polygon['polygon'])
        # Approximate lat/lon boundaries of continental US
        axes.set_xlim([-125, -67])
        axes.set_ylim([24, 50])
        axes.set_aspect(1)
        pyplot.show()

def allowed_gai_family():
    return socket.AF_INET

parser = argparse.ArgumentParser()
parser.add_argument('--ipv6', action='store_true', help='Use ipv6')
parser.add_argument('--graph', action='store_true', help='Show graph')
parser.add_argument('--date', help='Use this date instead of the current one')
parser.add_argument('--location', help='latitude,longitude')
args = parser.parse_args()

if not args.ipv6:
    urllib3_cn.allowed_gai_family = allowed_gai_family
dt = datetime.datetime.now(datetime.timezone.utc)
if args.date:
    dt = datetime.datetime.fromisoformat(args.date)
mycoords = numpy.array([-90.50483, 41.44777])
if args.location:
    location = args.location.split(',')
    lat = float(location[0])
    lon = float(location[1])
    mycoords = numpy.array([lon, lat])
url = construct_url(dt)
r = requests.get(url)
parse_geojson(r.json(), mycoords, args.graph)
