import os
import requests
import certifi
import pymongo
from pymongo import MongoClient
from bs4 import BeautifulSoup
import requests
from random import choice
import json
from datetime import datetime,timezone

DATABASE = os.environ['DATABASE']
COLLECTION = os.environ['COLLECTION']
PASSWORD = os.environ['PASSWORD']

def proxy_generator():
    response = requests.get("https://sslproxies.org/")
    soup = BeautifulSoup(response.content, 'html5lib')
    proxies = choice(list(map(lambda x:x[0]+':'+x[1], list(zip(map(lambda x:x.text, soup.findAll('td')[::8]), map(lambda x:x.text, soup.findAll('td')[1::8]))))))
    proxy = {"http": "http://{}".format(proxies)}
    return proxy

def extract(job, page):

    #job = "ecommerace, google ads media buyer"
    Location = "remote"

    try:
        proxy = proxy_generator()
        print(proxy)

        url = f'https://www.simplyhired.com/search?q={job}&l={Location}&pn={page}'
        
        r = requests.get(url, proxies=proxy, timeout=7)
        soup = BeautifulSoup(r.content, 'html.parser')
        return soup

    except:
        print("connection error")
        pass

def extract_sum(link):
    try:
        proxy = proxy_generator()
       
        url = f'https://www.simplyhired.com{link}'
        
        r = requests.get(url, proxies=proxy, timeout=7)
        job_data = r.text
        soup = BeautifulSoup(job_data, 'html.parser')
        return soup

    except:
        print("connection error")
        pass


def find_sum(link):
    c = extract_sum(link)
    try:
        job = c.find('div', class_ = "viewjob-jobDescription")
        parsed_job = job.find('div', class_ = "p").get_text(strip=True, separator="\n")
    except:
        return "no job description available"
    return parsed_job

def find_image(link):
    c = extract_sum(link)
    try: 
        image_class = c.find('img', class_ = "viewjob-company-logoImg")
        photo_link = image_class.get("src")
        photo_link = f'http://simplyhired.com{photo_link}'
    except:
        photo_link = ""

    return photo_link

def transform(soup, job_type):
    divs = soup.find_all('div', class_ = "SerpJob-jobCard")
    count = 0

    # iterate through the div 
    for item in divs:
        if count == 6:
            break

        for link in item.find_all('a'):
            try:
                job_href = link.get('href')
            except:
                continue
            
        
        title = item.find('a').text.strip()

        # find company name via the span element and class name
        company = item.find('span', class_ = 'jobposting-company').text.strip()
    
        # attempt to find salary 
        try:
            salary = item.find('div', class_ = "jobposting-salary").text.strip()
          
        except: 
            break
       
        # job description
        summary = find_sum(job_href)

        # job link
        image_link = find_image(job_href)
        # utc timestamp
        date_time = datetime.now(timezone.utc)
        
        
        jobs = {'title': title, 'company': company, 'salary': salary, 'summary': summary, 'job_type': job_type, 'job_link': f'http://simplyhired.com{job_href}', 'image_link': image_link, 'time_sourced': date_time}
        
        count += 1
        
        # Append to the data sheet
        try:
            mycol.insert_one(jobs)
        except:
            print("Found duplicate")

if __name__ == "__main__":

    client = MongoClient(f'mongodb+srv://{COLLECTION}:{PASSWORD}@cluster0.7ec5s.mongodb.net/{DATABASE}?retryWrites=true&w=majority', tlsCAFile=certifi.where())
    try:
        print('connected bois')
    except Exception:
        print("unable to connect")
    

    mydb = client["mydatabase"]
    mycol = mydb["jobs"]

    # iterate through json file of job titles
    f = open('lighthouse/JobTypes.json', 'r')
    data = json.load(f)
    
    for i in data["job types"]:
        job_type = "ecommerce, " + i
        print(job_type)
        c = extract(job_type, 0)
        transform(c, i)

        # create an index to prevent adding duplicate jobs
        mycol.create_index([("title", pymongo.ASCENDING), ("company", pymongo.ASCENDING)], unique = True)
        
    
        #for j in range(1, 2, 1):
           # c = extract(i, j)
            #transform(c)

    #x = mycol.delete_many({})
    #print(x.deleted_count, "docs deleted")
    