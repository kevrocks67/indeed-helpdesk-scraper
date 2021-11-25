#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Title: Indeed Helpdesk Scraper
Author: Kevin Diaz
Description:
    Scrapes entry level IT Support job postings throughout the entire US
"""

import sys

from bs4 import BeautifulSoup
import requests

try:
    with open('webhook.txt', 'r') as hook_file:
        HOOK = hook_file.read().strip()
except FileNotFoundError:
    print("No webhook found in webhook.txt")
    sys.exit(1)

def get_data(query: str) -> str:
    """
    Make a query to indeed and retrieve the html data

    Args:
        query (str): The search query to be made on indeed
    Returns:
        resp (str): The html content of the response
    """
    url = f"https://www.indeed.com/jobs?q={query}"
    try:
        resp = requests.get(url).content
    except requests.ConnectionError as err:
        print("Could not connect: ", err)
        sys.exit(1)
    return resp

def scrape_html(html_content: str) -> list:
    """
    Scrapes the HTML content and creates a list of job postings structured as follows:
        job_posting = {
            "title": str,
            "link": str,
            "company": str,
            "location": str,
            "job_type": str,
            "salary": str,
        }
    Args:
        html_content (str): String of HTML data from indeed:
    Returns:
        postings (list[dict]): Contains list of job postings stored in dicts
    """
    postings = []

    soup= BeautifulSoup(html_content, 'html.parser')
    jobs = soup.findAll('a', class_='tapItem')

    for job in jobs:
        job_content = job.find('td', class_='resultContent')
        job_metadata = job_content.find('div', class_="metadata")

        job_title_spans = job_content.find(class_='jobTitle').find_all('span')
        if job_title_spans[0].text == 'new':
            job_title = job_title_spans[1].text
        else:
            job_title = job_title_spans[0].text

        postings.append({
                         "title": job_title,
                         "link": f"https://indeed.com/viewjob?jk={job['data-jk']}",
                         "company": job_content.find(class_='companyName').text,
                         "location": job_content.find(class_='companyLocation').text,
                         "job_type": "Full Time",
                         "salary": job_metadata.text if job_metadata else ""
                       })

    return postings

def publish_to_discord(postings: list) -> None:
    """
    Writes an embed to the defined discord webhook

    Args:
        postings (list[dict]): A list of dictionaries which each contain information
                              about a job posting.
    """

    for posting in postings:
        embed = {
              "content": "",
              "embeds": [
                {
                  "title": posting['title'],
                  "description": f"**Location**: {posting['location']}\n"
                                 f"**Company**: {posting['company']}\n"
                                 f"**Job Type**: {posting['job_type']}\n"
                                 f"**Salary**: {posting['salary']}",
                  "url": posting['link'],
                  "color": 5814783
                }
              ]
            }

        requests.post(HOOK, json=embed)

        print(embed)

def main():
    """
    Gets data from indeed and executes the scraper on it
    """
    query = "help%20desk%20OR%20it%20support%20OR%20desktop%20support&"\
            "l=United%20States&"\
            "explvl=entry_level&"\
            "fromage=1&"\
            "jt=fulltime&"\
            "limit=50"
    raw_content = get_data(query)
    postings = scrape_html(raw_content)
    publish_to_discord(postings)

if __name__ == "__main__":
    main()
