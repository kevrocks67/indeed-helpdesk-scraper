#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Title: Indeed Helpdesk Scraper
Author: Kevin Diaz
Description:
    Scrapes entry level IT Support job postings on indeed
"""

import sys

from bs4 import BeautifulSoup
import requests
import yaml


def get_data(query: str, country: str) -> str:
    """
    Make a query to indeed and retrieve the html data

    Args:
        query (str): The search query to be made on indeed
        country (str): Country code for indeed
    Returns:
        resp (str): The html content of the response
    """
    if country.lower() == 'us':
        url = f"https://www.indeed.com/jobs?q={query}"
    else:
        url = f"https://{country}.indeed.com/jobs?q={query}"

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
    jobs = soup.findAll('div', class_='tapItem')

    for job in jobs:
        job_content = job.find('td', class_='resultContent')
        job_metadata = job_content.find('div', class_="metadata")

        job_title_header = job_content.find(class_='jobTitle')
        job_title_spans = job_title_header.find_all('span')
        job_key = job_title_header.contents[-1]['data-jk']

        if job_title_spans[0].text == 'new':
            job_title = job_title_spans[1].text
        else:
            job_title = job_title_spans[0].text

        postings.append({
                         "title": job_title,
                         "link": f"https://indeed.com/viewjob?jk={job_key}",
                         "company": job_content.find(class_='companyName').text,
                         "location": job_content.find(class_='companyLocation').text,
                         "job_type": "Full Time",
                         "salary": job_metadata.text if job_metadata else ""
                       })

    return postings

def publish_to_discord(postings: list, webhook: str) -> None:
    """
    Writes an embed to the the discord webhook provided

    Args:
        postings (list[dict]): A list of dictionaries which each contain information
                              about a job posting.
        webhook (str): The discord webhook to which postings should be sent
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

        requests.post(webhook, json=embed)

        print(embed)

def main():
    """
    Loads config file, gets data from indeed, and executes the scraper on it
    """
    try:
        with open('countries.yml', 'r') as countries_file:
            countries = yaml.safe_load(countries_file)
    except FileNotFoundError:
        print("No countries.yml file found")
        sys.exit(1)

    for country in countries:
        search_query = ""

        for idx, search_key in enumerate(country['search_keys'], start=1):
            if idx < len(country['search_keys']):
                search_query += f"%22{search_key}%22%20OR"
            else:
                search_query += f"%22{search_key}%22&"

        query = search_query + \
                "explvl=entry_level&"\
                "fromage=1&"\
                "jt=fulltime&"\
                "limit=50"

        raw_content = get_data(query, country['country'])
        postings = scrape_html(raw_content)
        publish_to_discord(postings, country['webhook'])

if __name__ == "__main__":
    main()
