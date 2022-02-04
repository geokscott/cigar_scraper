# cigar_list.py
# This is a simple scraper, no multi threading or async operations
# This builds a CSV file of all cigars scrapped from specific list of web pages (per the pages[] list in the code) by: brand, name, & size
# Running the script multiple times will build on the CSV list and not create duplicates.
# I run this daily to compile a list of all cigars that ever show up on the website.

import requests
import bs4
from datetime import datetime
import csv
import itertools
import sys

import os

timestamp = datetime.now().strftime("%m/%d/%Y %H:%M")

def cleanup(x):
    """
    Returns a string with space on the left and right removed.
    """
    try:
        x = x.replace("Length (in inches):", "L:")
        x = x.replace("LENGTH:", "L:")
        x = x.replace("Ring Guage:", "RG:")
        x = x.replace("Ring Gauge:", "RG:")
        x = x.replace("RING GAUGE:", "RG:")
        x = x.replace("No Discounts Apply", "")
        x = x.replace("no discounts apply", "")
        x = ' '.join([line.strip() for line in x.strip().splitlines()])
    except:
        x = 'cleanup function error!'
    return x


def number_of_lines(fname):
    def _make_gen(reader):
        b = reader(2 ** 16)
        while b:
            yield b
            b = reader(2 ** 16)

    with open(fname, "rb") as f:
        count = sum(buf.count(b"\n") for buf in _make_gen(f.raw.read))
    return count


# START
file_name = os.path.join(sys.path[0], 'cigar_list.csv')
rows = []
rows.append(['Brand', 'Name', 'Size'])

# CoH
base_url = "https://www.cigarsofhabanos.com/"
pages = ['cigars-bolivar',
        'cigars-cohiba',
        'cigars-cuaba',
        'cigars-diplomaticos',
        'cigars-el-rey-del-mundo',
        'cigars-fonseca',
        'cigars-guantanamera',
        'cigars-h.upmann',
        'cigars-hoyo-de-monterrey',
        'cigars-jose-l.-piedra',
        'cigars-juan-lopez',
        'cigars-la-flor-de-cano',
        'cigars-la-gloria-cubana',
        'cigars-montecristo',
        'cigars-partagas',
        'cigars-por-larranaga',
        'cigars-punch',
        'cigars-quai-dorsay',
        'cigars-quintero-y-hermano',
        'cigars-rafael-gonzalez',
        'cigars-ramon-allones',
        'cigars-romeo-y-julieta',
        'cigars-saint-luis-rey',
        'cigars-san-cristobal-de-la-habana',
        'cigars-sancho-panza',
        'cigars-trinidad',
        'cigars-vegas-robaina',
        'cigars-vegueros']

for page in pages:
    url = f'{base_url}{page}'
    brand = page.split('-', 1)[1].replace('-', ' ')

    try:
        # get the page
        response = requests.get(url)
        # Save the response to soup
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        # Get number of items
        total_product_tags = len(soup.find_all('span',  {'class': ['product_header', 'product_header_W']}))
        # Iterate through all products
        for i in range (0, total_product_tags):
            name =  soup.find_all('span', {'class': ['product_header', 'product_header_W']})[i].get_text().strip()
            size = cleanup(soup.find_all('td', class_='nortxt')[i].find('div', class_='fsize11').get_text())
            rows.append([brand, name, size])
    except Exception as e:
        #this website didn't respond or the page had errors
        print(e)

# Open existing file for comparison
try:
    with open(file_name, 'r', newline='', encoding='ISO-8859-1') as existing_file:
        reader = csv.reader(existing_file)
        existing_rows = list(reader)
except:
    #file does not exist
    existing_rows = []
        
# Combine the existing rows with what was just scrapped, sort, then remove dups
combined_rows = existing_rows + rows
combined_rows.sort()
unique_rows = list(combined_rows for combined_rows,_ in itertools.groupby(combined_rows))

# Create new file with combined results
with open(file_name, 'w', newline='', encoding='ISO-8859-1') as csvfile:
    writer = csv.writer(csvfile)
    for row in unique_rows:
        writer.writerow(row)

total_lines = number_of_lines(file_name)
print(f'File created {timestamp} with {total_lines} lines.')
