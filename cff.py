from rich import print
from rich.panel import Panel
from rich.columns import Columns

import sqlite3
from sqlite3 import Error

from bs4 import BeautifulSoup
from urllib.request import urlopen

from os import path
from datetime import datetime, timedelta

from cffconfig import cff_config as cf


DB_LINK = path.dirname(__file__)+'/stuff.db'

def run():
    print('Welcome to Craigslist Free Finder. Make sure you are running in fullscreen and your cffconfig file is properly set up. Have fun with the free stuff!\n')
    input('Press Enter to Continue:')
    validate_config()
    prev_data = get_previous_data()
    new_data = search_craigslist(prev_data)
    print_output(new_data)
    update_db(new_data, cf['RESET'])

def validate_config():
    #check config file
    for config_key in cf:
        if cf[config_key] == None:
            raise ValueError("Config file isn't set up properly")

def get_previous_data()->list:
    #check for database
    print(DB_LINK)
    if not path.exists(DB_LINK):
        #make database if none exists   
        create_database()
    #get recent search data
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("""SELECT title, link 
                   FROM stuff""")
    prev_data = cur.fetchall()
    return prev_data

def create_database():
    sql_create_table = """CREATE TABLE IF NOT EXISTS stuff (
                            id integer PRIMARY KEY,
                            title text,
                            link text
                        );"""
    print(DB_LINK)
    conn = create_connection(DB_LINK)
    try:
        cur = conn.cursor()
        cur.execute(sql_create_table)
    except Error as e:
        print(e)

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_LINK)
        return conn
    except Error as e:
        print(e)
    return conn

def search_craigslist(prev_data):
    urls = _create_urls()
    new_data = []
    #perform web search
    for url in urls:
        #new data gets passed into the function to prevent the addition of duplicates
        new_data.extend(get_search_data(url, new_data+prev_data))
    return new_data

#createes a list of the items
def _create_urls()->list[str]:
    urlpattern = "https://{}.craigslist.org/search/zip?sort=date&search_distance={}&postal={}&query={}"
    urls = [urlpattern.format(cf['CITY'], cf['RADIUS'], cf['ZIPCODE'], x) for x in cf['PHRASES']]
    return urls

#gets the links and post titles of search results
def get_search_data(url:str, existing_data:list[tuple])->list[tuple]:
    new_data = []
    #use bs4 to get list of (title, link) from webpage
    try:
        print(url)
        page = urlopen(url)
    except:
        print('error opening Url')
        return
    soup = BeautifulSoup(page, 'html.parser')
    results = soup.find_all('li', {'class':'result-row'})
    for result in results:
        result_data = result.find('a', {'class':'result-title'})
        distance = result.find('span', {'class':'maptag'})
        if float(distance.string[:-2]) > cf['RADIUS']:
            continue
        new_entry = (result_data.string, result_data.get("href"))
        if new_entry in existing_data:
            continue
        new_data.append(new_entry)
    return new_data

# create rich text layout ready to diaplsy to the user
def print_output(new_data):
    panels = [Panel('[link]{}[/link]'.format(x[1]), 
                    title='[yellow]{}[/yellow]'.format(x[0]),
                    height=3)
                    for x in new_data]
    print(Columns(panels))
    
    
#credate
def update_db(new_data, reset=False):
    conn = create_connection()
    cur = conn.cursor()
    if reset:
        #delete database
        cur.execute('DROP * from stuff')
    for datum in new_data:
        cur.execute(""" INSERT INTO stuff (title, link)
                        VALUES (?, ?)""", datum)
    conn.commit()

if __name__=="__main__":
    run()

