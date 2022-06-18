### Job Scraper 

Web scraper that uses BeautifulSoup to scrape a list of E-commerace related jobs from SimplyHired and appends the job details into a MongoDB database. Each job is indexed to prevent duplicates from being added into the DB. Each request uses a different ip address pulled from the rotating proxy function.