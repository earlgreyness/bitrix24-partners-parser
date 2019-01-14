#!/usr/bin/env python3
import csv
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

import attr
import requests
from bs4 import BeautifulSoup

HOST = 'https://www.bitrix24.ru'


@attr.s
class Contact:
    name = attr.ib(default='')
    url = attr.ib(default='')
    website = attr.ib(default='')
    phones = attr.ib(default='')


def extract_url(soup):
    link = soup.find('a', class_='bp-partner-list-item-name')

    url = HOST + link.get('href')
    phones = soup.find('div', class_='bp-partner-request-phone').string

    return url


def download_partners(page):
    payload = dict(
        ajax='Y',
        page_n=page,
    )
    resp = requests.post(HOST + '/partners/', data=payload)
    html = resp.json()['html']
    return BeautifulSoup(html, 'html.parser')


def download_detailed_info(url):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    try:
        name = soup.find('h2', class_='bx-pdl-header-title-name-content').string
    except AttributeError:
        return None
    website = soup.find('a', class_='pt_card_hd_link').string.strip()

    description = soup.find('div', class_='bx-pdl-description-contacts-content')

    # print('='*100)
    # for tag in description.find_all('p', recursive=False):
    #     print(tag)

    return Contact(
        name=name,
        url=url,
        website=website,
    )


def main():
    page = 1
    stop = False
    partners = OrderedDict()

    while True:
        soup = download_partners(page)
        divs = soup.find_all('div', class_='bp-partner-list-item-cnr')

        for url in [extract_url(x) for x in divs]:
            if url in partners:
                stop = True
                break
            else:
                partners[url] = None

        if stop:
            break

        print('Parsed page', page)
        page += 1

    urls = list(partners.keys())

    with ThreadPoolExecutor() as executor:
        for i, contact in enumerate(executor.map(download_detailed_info, urls), start=1):
            partners[contact.url] = contact
            print('Done {}/{}: {}'.format(i, len(urls), contact))

    contacts = [x for x in partners.values() if x is not None]

    pprint(contacts)
    pprint(len(contacts))
    pprint(page)

    with open('bitrix24-partner-contacts.csv', 'w') as file:
        writer = csv.writer(file)

        for contact in contacts:
            writer.writerow([contact.name, contact.url, contact.website])


if __name__ == '__main__':
    main()
