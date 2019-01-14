#!/usr/bin/env python3
import csv
import pickle
import re
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pprint import pprint

import attr
import requests
from bs4 import BeautifulSoup
from phonenumbers import (
    NumberParseException, PhoneNumberFormat, parse as parse_phonenumber,
    format_number, is_possible_number, is_valid_number,
)

HOST = 'https://www.bitrix24.ru'
DIGITS = set('0123456789+()')


@attr.s
class Contact:
    name = attr.ib()
    url = attr.ib()
    phones = attr.ib()


def extract_contact(soup):
    print(soup)
    print('-' * 100)

    link = soup.find('a', class_='bp-partner-list-item-name')

    name = link.string
    url = HOST + link.get('href')
    phones = soup.find('div', class_='bp-partner-request-phone').string

    return Contact(
        name=name,
        url=url,
        phones=phones,
    )


def download_partners(page):
    payload = dict(
        ajax='Y',
        page_n=page,
    )
    resp = requests.post(HOST + '/partners/', data=payload)
    html = resp.json()['html']
    return BeautifulSoup(html, 'html.parser')


def main():
    contacts = []
    page = 1
    names = set()

    while True:
        soup = download_partners(page)
        divs = soup.find_all('div', class_='bp-partner-list-item-cnr')
        new_contacts = [extract_contact(x) for x in divs]
        new_names = {x.name for x in new_contacts}
        if names & new_names:
            break
        contacts.extend(new_contacts)
        names.update(new_names)
        print('Parsed page', page)
        page += 1

    pprint(contacts)
    pprint(len(contacts))
    pprint(page)

    with open('bitrix24-partner-contacts.csv', 'w') as file:
        writer = csv.writer(file)

        for contact in contacts:
            writer.writerow([contact.name, contact.url, contact.phones])


if __name__ == '__main__':
    main()
