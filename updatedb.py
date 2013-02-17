#!/usr/bin/env python3

from myougiden import *
import urllib.request
import sqlite3 as sql
# import lxml.etree as ET
import xml.etree.cElementTree as ET

def create_table(cur):
    # what about a custom collation function?

    # my version of sqlite3 doesn't seem to work with executemany()
    cur.execute('DROP TABLE IF EXISTS kanjis;')
    cur.execute('DROP TABLE IF EXISTS readings;')
    cur.execute('DROP TABLE IF EXISTS senses;')
    cur.execute('DROP TABLE IF EXISTS entries;')

    cur.execute('''
      CREATE TABLE 
      entries (
        ent_seq INTEGER PRIMARY KEY
      );
    ''')

    cur.execute('''
      CREATE TABLE 
      kanjis (
        ent_seq INTEGER NOT NULL,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji TEXT NOT NULL,
        FOREIGN KEY (ent_seq) REFERENCES entries(ent_seq)
      );
    ''')

    cur.execute('''
      CREATE TABLE 
      readings (
        ent_seq INTEGER NOT NULL,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reading TEXT NOT NULL,
        FOREIGN KEY (ent_seq) REFERENCES entries(ent_seq)
      );
    ''')

    cur.execute('''
      CREATE TABLE 
      senses (
        ent_seq INTEGER NOT NULL,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sense TEXT NOT NULL,
        FOREIGN KEY (ent_seq) REFERENCES entries(ent_seq)
      );
    ''')

    cur.execute('''
      CREATE INDEX kanjis_ent_seq ON kanjis (ent_seq);
    ''')
    cur.execute('''
      CREATE INDEX readings_ent_seq ON readings (ent_seq);
    ''')
    cur.execute('''
      CREATE INDEX senses_ent_seq ON senses (ent_seq);
    ''')

    cur.execute('''
      CREATE INDEX kanjis_kanji ON kanjis (kanji);
    ''')
    cur.execute('''
      CREATE INDEX readings_reading ON readings (reading);
    ''')
    cur.execute('''
      CREATE INDEX senses_sense ON senses (sense);
    ''')


def insert_entry(cur, ent_seq, kanjis, readings, senses):
    cur.execute('INSERT INTO entries(ent_seq) VALUES (?);', [ent_seq])
    for kanji in kanjis:
        cur.execute('INSERT INTO kanjis(ent_seq, kanji) VALUES (?, ?);', [ent_seq, kanji])

    for reading in readings:
        cur.execute('INSERT INTO readings(ent_seq, reading) VALUES (?, ?);', [ent_seq, reading])

    for sense in senses:
        cur.execute('INSERT INTO senses(ent_seq, sense) VALUES (?, ?);', [ent_seq, sense])

def make_database(jmdict, sqlite):
    con, cur = opendb()
    tree = ET.parse(jmdict)

    create_table(cur)

    for entry in tree.findall('entry'):
        ent_seq = entry.find('ent_seq').text

        kanjis = []
        for kanji in entry.findall('k_ele'):
            kanjis.append(kanji.find('keb').text)

        readings = []
        for reading in entry.findall('r_ele'):
            readings.append(reading.find('reb').text)

        senses = []
        for sense in entry.findall('sense'):

            # for now I foresee no need for a separate glosses table
            glosses = []
            for gloss in sense.findall('gloss'):
                glosses.append(gloss.text)
            senses.append('; '.join(glosses))

        insert_entry(cur, ent_seq, kanjis, readings, senses)

    cur.close()
    con.commit()

def fetch_jmdict(outfile):
    req = urllib.request.urlretrieve(PATHS['jmdict_url'], outfile)

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()

    ap.add_argument('-j', '--jmdict', default='./JMdict_e.gz', metavar='PATH',
                    help="Path to JMdict_e.gz file (default: %(default)s)")

    ap.add_argument('-f', '--fetch', action='store_true',
                    help=("Try to fetch JMdict_e.gz from %s" % PATHS['jmdict_url']))

    args = ap.parse_args()

    if args.fetch:
        print("Fetching %s from %s, please wait..." % (args.jmdict, PATHS['jmdict_url']))
        fetch_jmdict(args.jmdict)

    print("Updating database at %s from %s, please wait..." %
          (PATHS['database'], args.jmdict))
    make_database(gzip.open(args.jmdict, 'r'),
                  PATHS['database'])


