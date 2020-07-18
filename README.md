# cigar_scraper
web scraper for cigar site

This is my first attemp at web scraping. This will scrape the https://www.cigarsofhabanos.com website for all cuban cigars on sale and send you a nicely formatted HTML message with all cigars on sale along with sale details and links to the website.  The script uses a config.yaml file to hold your email configuration, the sample.yaml file shows the format for this file.

I'm using concurrent processing to reuqest 28 pages at once, then processing the content of those page requests, all in about 10 seconds.

Sample email output:

![Alt text](example.png?raw=true "Example")


