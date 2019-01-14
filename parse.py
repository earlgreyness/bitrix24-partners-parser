#!/usr/bin/env python3
import csv
import pickle
import re
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import attr
import requests
from bs4 import BeautifulSoup
from phonenumbers import (
    NumberParseException, PhoneNumberFormat, parse as parse_phonenumber,
    format_number, is_possible_number, is_valid_number,
)

AMO_HOST = 'https://www.amocrm.ru'
DIGITS = set('0123456789+()')
