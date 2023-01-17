#!/home/george/env/bin/python
# encoding: utf-8

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
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


def cleanup(x):
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


def fetch_page(page):
    #time.sleep(1)  # in case the website balks at too many request at once from the same IP
    url = f'{base_url}{page}'
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)    
    response = session.get(url)
    return response


def process_page(response):
    cigars = []
    try:
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        # Get number of products on the page
        total_product_tags = len(soup.find_all(
            'span',  {'class': ['product_header', 'product_header_W']}))
        # Iterate through products
        for i in range(0, total_product_tags):
            name = soup.find_all('span', {'class': ['product_header', 'product_header_W']})[i].get_text()
            url = soup.find('form', id='frmDetails').get('action')
            description = f'<a href={base_url}{url}>{name}</a>'
            price = cleanup(soup.find_all('span', class_='redtxt1_strikeout')[i].get_text())
            size = cleanup(soup.find_all('td', class_='nortxt')[i].find('div', class_='fsize11').get_text())
            quantity = cleanup(soup.find_all('tr', class_='nortxt')[i].find('td', class_='fsize11').get_text())
            try:
                sale_price = cleanup(soup.find_all('td', class_='pricetxt')[i].get_text())
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


def format_output(cigars):

    # Build HTML email Header
    html = f'<p><a href={base_url}>Cigars of Habanos</a></p>'

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
            color = 'cyan'
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


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
        responses = executor.map(fetch_page, pages)

        cigars = []
        for response in responses:
            cigar_list = process_page(response)
            for cigar in cigar_list:
                cigars.append(cigar)

        html_results = format_output(cigars)

        # Send email
        part2 = MIMEText(html_results, 'html')
        msg.attach(part2)
        s = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        s.login(emailuser, emailpassword)
        s.sendmail(emailfrom, emailto, msg.as_string())
        s.close()
    
        runtime = round(time.time() - start_time, 2)
        print(f'Created: {timestamp} - Runtime: {runtime} seconds')
