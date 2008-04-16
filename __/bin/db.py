#!/usr/bin/env python
"""Update the database from the txt/csv file.

First run "__/bin/db.py create", then run this script without arguments: it 
should find the points.txt and points.db files.

"""
import math
import os
import sqlite3
import stat
import sys
from datetime import datetime
from StringIO import StringIO

import aspen
root = aspen.find_root()
aspen.configure(['--root', root])

sys.stdout = StringIO()
from geopy import distance # why junk at import-time?!
sys.stdout = sys.__stdout__


__all__ = ['clear', 'count', 'create', 'delete', 'intensify', 'main',
           'normalize', 'sync']


THRESHOLD = 20 # distance in miles within which points must be of each other

# Set up some helpers for roughly converting degrees to miles.
# ============================================================
# These are based off of manual calculations at:
#   http://www.csgnetwork.com/degreelenllavcalc.html

ROUGH_MILE_DEGREE = 70.0
ROUGH_LAT = 1.0/ROUGH_MILE_DEGREE * THRESHOLD
def ROUGH_LNG(lat):
    lat = (lat - ROUGH_LAT) if (lat >= 0) else (lat + ROUGH_LAT)
    lat_mile_degree = (lat / 90.0) * ROUGH_MILE_DEGREE
    miles = 1.0/lat_mile_degree * THRESHOLD
    return miles

RAWPATH = os.path.join(aspen.paths.__, 'var', 'points.txt')
DBPATH = os.path.join(aspen.paths.__, 'var', 'points.db')


def create():
    cur = CONN.cursor()
    cur.execute("""

        CREATE TABLE IF NOT EXISTS points(

            uid         TEXT UNIQUE PRIMARY KEY             ,
            lat         REAL                                ,
            lng         REAL                                ,

            intensity   REAL DEFAULT 1.0                    ,
            modtime     TIMESTAMP                           ,
            seentime    TIMESTAMP

        );

    """)


def clear():
    cur = CONN.cursor()
    cur.execute("DELETE FROM points")


def count():
    cur = CONN.cursor()
    cur.execute("SELECT COUNT(id) FROM points")
    print cur.fetchone()[0]


def delete():
    os.remove(DBPATH)


def intensify():
    """Calculate intensities for each point.
    """

    sys.stdout.write('intensifying'); sys.stdout.flush()

    cur = CONN.cursor()
    cur.execute("SELECT * FROM points")
    points = list(cur)
    cur.close() # only one connection at a time on Windows?

    for point in points:

        # Select points roughly within the limit.
        # =======================================
        # This saves us a lot of time.

        n = point['lat'] + ROUGH_LAT
        s = point['lat'] - ROUGH_LAT
        e = point['lng'] + ROUGH_LNG(point['lat'])
        w = point['lng'] - ROUGH_LNG(point['lat'])

        others = CONN.cursor()
        others.execute("""

            SELECT *
              FROM points
             WHERE lat <= ?
               AND lat >= ?
               AND lng <= ?
               AND lng >= ?

        """, (n,s,e,w))


        # Narrow down to only points actually within the limit.
        # =====================================================

        intensity = 0
        for other in others:
            d = distance.distance( (point['lat'], point['lng'])
                                 , (other['lat'], other['lng'])
                                  )
            km = d.calculate() # accounts for 0
            if (km == 0) or (d.miles <= THRESHOLD):
                intensity += 1

        cur = CONN.cursor()
        cur.execute( "UPDATE points SET intensity = ? WHERE uid = ?"
                   , (intensity, point['uid'])
                    )

        sys.stdout.write('.'); sys.stdout.flush()

    print 'done'


def main():
    """Update the database.
    """
    sync()
    intensify()
    normalize()


def normalize():
    """Normalize intensities.
    """

    sys.stdout.write('normalizing'); sys.stdout.flush()

    hist = {}

    cur = CONN.cursor()
    cur.execute("SELECT * FROM points")
    points = list(cur)
    cur.close() # only one connection at a time on Windows?
    
    update = CONN.cursor()

    for point in points:
        assert point['intensity'] >= 1.0
        normalized_intensity = (100 - (100.0 / point['intensity'])) / 100.0
        update.execute( "UPDATE points SET intensity = ? WHERE uid = ?"
                      , (normalized_intensity, point['uid'])
                       )
        sys.stdout.write('.'); sys.stdout.flush()

    print 'done'

#        if normalized_intensity in hist:
#            hist[normalized_intensity] += 1
#        else:
#            hist[normalized_intensity] = 1
#
#
#    for k, v in sorted(hist.items()):
#        print "%0.6f" % k, ('#'*v)


def sync():
    """Synchronize points.db with points.txt.
    """

    sys.stdout.write('syncing'); sys.stdout.flush()

    cur = CONN.cursor()
    modtime = datetime.fromtimestamp(os.stat(RAWPATH)[stat.ST_MTIME])

    for point in open(RAWPATH, 'r'):

        # Parse and validate values.
        # ==========================

        assert point.count(',') == 2, "bad line: " + point
        uid, lat, lng = point.split(',')
        try:
            lat = float(lat)
            lng = float(lng)
        except:
            print "bad line:", point


        # Select any existing record for this point.
        # ==========================================
        # After this, 'point' will either be None or a sqlite3.Row.

        result = cur.execute( "SELECT * FROM points WHERE uid = ?"
                            , (uid,)
                             )
        result = result.fetchall()
        numresults = len(result) if (result is not None) else 0
        if numresults not in (0, 1):
            msg = "%d result[s]; wanted 0 or 1" % numresults
            print "bad record: <%s> [%s]" % (uid, msg)
        point = result[0] if (numresults == 1) else None


        # Insert the point if we don't have it.
        # =====================================

        if point is None:
            sys.stdout.write('O'); sys.stdout.flush()
            cur.execute("""

                INSERT INTO points
                            (uid, lat, lng, modtime, seentime)
                     VALUES (  ?,   ?,   ?,        ?,    ?)

            """, (uid, lat, lng, modtime, modtime))


        # Update the point if it has changed.
        # ===================================

        elif (point['lat'], point['lng']) != (lat, lng):
            sys.stdout.write('o'); sys.stdout.flush()
            #print (point['lat'], point['lng']), '!=', (lat, lng)

            cur.execute("""

                UPDATE points
                   SET lat = ?
                     , lng = ?
                     , modtime = ?
                     , seentime = ?
                 WHERE uid = ?

            """, (lat, lng, modtime, modtime, uid))


        # If it hasn't changed, at least mark it as seen.
        # ===============================================
        # Otherwise we will delete it presently.

        else:
            sys.stdout.write('.'); sys.stdout.flush()
            cur.execute( "UPDATE points SET seentime = ? WHERE uid = ?"
                       , (modtime, uid)
                        )


    # Now delete rows that weren't in the latest txt file.
    # ====================================================

    cur.execute("DELETE FROM points WHERE seentime != ?", (modtime,))

    print 'done'


if __name__ == '__main__':

    try:
        subc = sys.argv[1]
    except IndexError:
        subc = 'main'

    if subc not in __all__:
        raise SystemExit("I wonder, what does '%s' mean?" % subc)

    if subc not in ('create', 'delete'):
        if not os.path.isfile(DBPATH):
            raise SystemExit("Please create the db first with 'create'.")

    CONN = sqlite3.connect(DBPATH)
    CONN.row_factory = sqlite3.Row # gives us key access
    func = globals()[subc]
    func()
    CONN.commit()
    CONN.close()
