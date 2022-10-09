#!/home/george/env/bin/python
# encoding: utf-8

import aiohttp
import asyncio
import requests
import bs4
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import concurrent.futures
import yaml
import os
import time

start_time = time.time()
timestamp = datetime.now().strftime("%m/%d/%Y %H:%M")

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
try:
    with open(config_file) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
except:
    print("Your config.yaml file is missing!")
    quit()
    
# Setup email
emailto = config['emailto']
emailfrom = config['emailfrom']
SMTP_SERVER = config['SMTP_SERVER']
SMTP_PORT = config['SMTP_PORT']
emailuser = config['emailuser']
emailpassword = config['emailpassword']
msg = MIMEMultipart('alternative')
msg['Subject'] = "Cigars on Sale @ COH"
msg['From'] = emailfrom
msg['To'] = ','.join(emailto)

# Define what will be scraped
# CoH website
base_url = "https://www.cohcigars.com/"

# pages we are going to scrape
pages = ['cigars-bolivar',
         'cigars-cohiba',
         'cigars-diplomaticos',
         'cigars-el-rey-del-mundo',
         'cigars-h.upmann',
         'cigars-hoyo-de-monterrey',
         'cigars-juan-lopez',
         'cigars-la-gloria-cubana',
         'cigars-montecristo',
         'cigars-por-larranaga',
         'cigars-punch',
         'cigars-ramon-allones',
         'cigars-saint-luis-rey',
         'cigars-san-cristobal-de-la-habana',
         'cigars-trinidad',
         'cigars-vegas-robaina'
         ]

#         'cigars-cuaba',
#         'cigars-fonseca',
#         'cigars-guantanamera',
#         'cigars-jose-l.-piedra',
#         'cigars-la-flor-de-cano',
#         'cigars-partagas',
#         'cigars-quai-dorsay',
#         'cigars-quintero-y-hermano',
#         'cigars-rafael-gonzalez',
#         'cigars-romeo-y-julieta',
#         'cigars-sancho-panza',
#         'cigars-vegueros',

async def cleanup(x):
    """
    Returns a 'cleaned-up' string with spaces on the left and right removed.
    """
    try:
        x = x.lower()
        x = x.replace("us$", "")
        x = x.replace("~usd", "")
        x = x.replace("$", "")
        x = x.replace("no discounts apply", "")
        x = x.replace("slb cabinet of", "SLB")
        x = x.replace("box", "Box")
        x = x.replace("length (in inches):", "L:")
        x = x.replace("length:", "L:")
        x = x.replace("ring gauge:", "RG:")
        x = ' '.join([line.strip() for line in x.strip().splitlines()])
    except:
        x = 'clean-up function error!'
    return x


async def process_page(response):
    cigars = []
    try:
        soup = bs4.BeautifulSoup(response, "html.parser")
        # Get number of products on the page
        total_product_tags = len(soup.find_all(
            'span',  {'class': ['product_header', 'product_header_W']}))
        # Iterate through products
        for i in range(0, total_product_tags):
            name = soup.find_all('span', {'class': ['product_header', 'product_header_W']})[i].get_text()
            url = soup.find('form', id='frmDetails').get('action')
            description = f'<a href={base_url}{url}>{name}</a>'
            price = await cleanup(soup.find_all('span', class_='redtxt1_strikeout')[i].get_text())
            size = await cleanup(soup.find_all('td', class_='nortxt')[i].find('div', class_='fsize11').get_text())
            quantity = await cleanup(soup.find_all('tr', class_='nortxt')[i].find('td', class_='fsize11').get_text())
            try:
                sale_price = await cleanup(soup.find_all('td', class_='pricetxt')[i].get_text())
                save = (float(price) - float(sale_price)) / float(price)
                save = f'{save:.0%}'
            except:
                sale_price = 0
                save = 0
            # if "red" price if found, it's a sale price, include it in the return
            if price:
                cigars.append([sale_price, price, save, description, quantity, size])

    except Exception as e:
        # this website didn't respond or the page had errors
        cigars.append(['', '', '', {e}, '', ''])

    return cigars


async def format_output(cigars):

    # Build HTML email Header
    html = "<p><a href=https://www.cigarsofhabanos.com/>Cigars of Habanos</a></p>"

    html += """<table border=1 cellspacing=0 cellpadding=2>
        <tr>
        <th style=background-color:gray>Sale</th>
        <th style=background-color:gray>Price</th>
        <th style=background-color:gray>Save</th>
        <th style=background-color:gray>Description</th>
        <th style=background-color:gray>Quantity</th>
        <th style=background-color:gray>Size</th>
        </tr>"""

    color = ''
    for cigar in cigars:
        # Toggle line color
        if color == 'lightcyan':
            color = 'lightgray'
        else:
            color = 'lightcyan'
        html += f"""<tr>
                <td style=background-color:{color}><b>{cigar[0]}</b></td>
                <td style=background-color:{color}>{cigar[1]}</td>
                <td style=background-color:{color}>{cigar[2]}</td>
                <td style=background-color:{color}>{cigar[3]}</td>
                <td style=background-color:{color}>{cigar[4]}</td>
                <td style=background-color:{color}>{cigar[5]}</td>
                </tr>"""

    html += "</table>"

    return html


async def get_page(session, url):
    cigar_list = []
    async with session.get(url) as response:
        html = await response.text()
        cigar_list = await process_page(html)
        return cigar_list


async def main():

    cigars = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in pages:
            url = f'{base_url}{page}'
            tasks.append(asyncio.ensure_future(get_page(session, url)))

        miltiple_cigar_lists = await asyncio.gather(*tasks)
        for cigar_list in miltiple_cigar_lists:
            for cigar in cigar_list:
                cigars.append(cigar)

        html_results = await format_output(cigars)

        # Send email
        part2 = MIMEText(html_results, 'html')
        msg.attach(part2)
        s = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        s.login(emailuser, emailpassword)
        s.sendmail(emailfrom, emailto, msg.as_string())
        s.close()

if __name__ == '__main__':
    asyncio.run(main())
    runtime = round(time.time() - start_time, 2)
    print(f'Created: {timestamp} - Runtime: {runtime} seconds')
