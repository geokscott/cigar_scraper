# cigar_scraper
web scraper for cigar site

This is my first attempt at web scraping. This will scrape the https://www.cigarsofhabanos.com website for a specific list of cuban cigars on sale and send a nicely formatted HTML message with cigars on sale along with details and links to the website.  The script uses a config.yaml file to hold your email configuration, the sample.yaml file shows the format for this file.

I'm using concurrent processing to request 28 pages at once, then processing the content of those page requests, all in about 10 seconds.

Sample email output:

![Alt text](example.png?raw=true "Example")
