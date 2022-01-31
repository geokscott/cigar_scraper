# cigar_scraper
Web scraper for a cigar website

This is my first attempt at web scraping. This specifically scrapes the https://www.cigarsofhabanos.com website for a named list of cuban cigar brands on sale and sends a nicely HTML formatted email message listing the cigars on sale along with details and links to the specific web page.  The script uses a config.yaml file to hold your specific email server configurations and email addresses, the sample.yaml file shows the format for this file.  Your config.yaml file must be located in the same folder as the script.

There are two version of the scaper:

**cigar_scrape.py:** Uses multiple threads. (takes about 38 seconds to process 27 page requests)

**cigar_scrape_async.py:** Uses asycronous processing with aiohttp and asyncio. (takes about 10 seconds)


Sample email output:

![Alt text](example.png?raw=true "Example")
