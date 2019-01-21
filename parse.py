#!/usr/bin/env python3
import csv
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
import pickle

import attr
import requests
from bs4 import BeautifulSoup

HOST = 'https://www.bitrix24.ru'


@attr.s
class Contact:
    name = attr.ib()
    url = attr.ib()
    website = attr.ib()
    phones = attr.ib()
    email = attr.ib()
    address = attr.ib()


def extract_url(soup):
    link = soup.find('a', class_='bp-partner-list-item-name')
    return HOST + link.get('href')


def download_partners_page(page):
    payload = {
        'ajax': 'Y',
        'page_n': page,
    }
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

    print('='*100)
    data = {}
    for tag in description.find_all('p', recursive=False):
        children = [x for x in tag if x != '\n']
        print(children)
        meta = children[0].string.strip()
        if 'E-mail' in meta:
            value = children[1].find_all('a')[0].string.strip()
        else:
            value = children[1].string.strip()
        data[meta] = value
        print(data)
        print('>'*100)

    return Contact(
        name=name,
        url=url,
        website=website,
        phones=data.get('Телефон:'),
        email=data.get('E-mail:'),
        address=data.get('Адрес:'),
    )


def download_partners():
    page = 1
    stop = False
    partners = OrderedDict()

    while True:
        soup = download_partners_page(page)
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

    return partners


def main():
    # partners = download_partners()
    # with open('partners.pickle', 'wb') as file:
    #     pickle.dump(partners, file)

    with open('partners.pickle', 'rb') as file:
        partners = pickle.load(file)

    urls = list(partners.keys())

    with ThreadPoolExecutor() as executor:
        for i, contact in enumerate(executor.map(download_detailed_info, urls), start=1):
            partners[contact.url] = contact
            print('Done {}/{}: {}'.format(i, len(urls), contact))

    contacts = [x for x in partners.values() if x is not None]

    pprint(contacts)
    pprint(len(contacts))

    with open('bitrix24-partner-contacts.csv', 'w') as file:
        writer = csv.writer(file)

        for contact in contacts:
            writer.writerow([
                contact.name, contact.url, contact.website, contact.email,
                contact.address, contact.phones,
            ])


if __name__ == '__main__':
    main()
