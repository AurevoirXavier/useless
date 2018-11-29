# --- std ---
import re


def all_cases(path: str = '.') -> map:
    # --- std ---
    from os import listdir

    def is_dir(d: str) -> bool:
        # --- std ---
        from os.path import isdir

        return not d.startswith('.') and isdir(d)

    def is_file(f: str) -> bool:
        # --- std ---
        from os.path import isfile

        return not f.startswith('.') and isfile(f)

    def filter_dir(fn: callable, parent: str) -> filter:
        return filter(fn, map(lambda descendant: f'{parent}/{descendant}', listdir(parent)))

    return map(lambda d: map(lambda f: filter_dir(is_file, f), filter_dir(is_dir, d)), filter(is_dir, listdir(path)))


def read_doc(f: str) -> filter:
    # --- std ---
    from os import remove, path
    from subprocess import DEVNULL, call
    # --- external ---
    from docx import Document

    def strip_doc(doc: list) -> filter:
        return filter(lambda _: _, map(lambda line: line.text.strip(), doc))

    def convert_doc(doc: str):
        call(['soffice', '--headless', '--convert-to', 'docx', doc, '--outdir', f'{path.dirname(doc)}'], stdout=DEVNULL)
        remove(doc)

    if f.endswith('.doc'):
        convert_doc(f)
        f = f'{f}x'

    print(f)

    return strip_doc(Document(f).paragraphs)


def get_case_id(lines: filter) -> str:
    for _ in range(2):
        next(lines)

    return next(lines)


def get_court(lines: filter) -> str:
    court = next(lines)
    court = re.match(r'公诉机关(.+)人民检察院', court).group(1)
    court = re.sub(r'.+省', '', court)

    return court


def parse_int(number: str) -> int:
    if number == '十':
        return 10
    elif number == '十万':
        return 100000

    def parse_int(x: str) -> str:
        return {
            '○': '0',
            '零': '0',
            '一': '1',
            '二': '2',
            '三': '3',
            '四': '4',
            '五': '5',
            '六': '6',
            '七': '7',
            '八': '8',
            '九': '9'
        }.get(x, '')

    return {
               '十': 10,
               '百': 100,
               '千': 1000,
               '万': 10000
           }.get(number[-1], 1) * int(''.join(map(parse_int, number)))


def parse_date(date: str) -> (int, int, int):
    matched = re.match(r'(.{4})年(.{1,})月(.{1,})日', date)
    try:
        return int(matched.group(1)), int(matched.group(2)), int(matched.group(3))
    except ValueError:
        return parse_int(matched.group(1)), parse_int(matched.group(2)), parse_int(matched.group(3))


def get_accuseds(lines: filter) -> list:
    line = next(lines)
    if '原告人' in line:  # skip accuser
        line = next(lines)

    accuseds = []
    while line.startswith('被告人'):
        matched = re.match(r'被告人(.+)，(.+)出', line)
        accused_name = matched.group(1).split('（')[0]
        accused_birthday = matched.group(2)
        accuseds.append((accused_name, accused_birthday))

        line = next(lines)
        if '辩护人' in line:  # skip attorney
            line = next(lines)

    return accuseds


def get_youngest_accuseds(accuseds: list) -> list:
    min_birthday = (0, 0, 0)
    for accused in accuseds:
        birthday = parse_date(accused[1])
        for i in range(3):
            if birthday[i] > min_birthday[i]:
                min_birthday = birthday
            elif birthday[i] < min_birthday[i]:
                break
    min_birthday = f'{min_birthday[0]}年{min_birthday[1]}月{min_birthday[2]}日'

    return list(filter(lambda accused: accused[1] == min_birthday, accuseds))


def get_detail(lines: filter) -> (set, list, set):
    # --- custom ---
    from conf import CONTACT_INFOS, DRUGS, DRUGS_SOURCE, PAYMENTS, QUANTIFIER, SHIPPINGS

    def get_contact_info(line: str, contact_infos: set):
        for contact_info in CONTACT_INFOS:
            if contact_info in line:
                contact_infos.add(contact_info)

    def get_drug(line: str, drugs: list):
        def split_int(text: str) -> (int, str):
            matched = re.match(r"([一二三四五六七八九十百千万]+|\d+)(.+)", text)
            number = matched.group(1)
            try:
                return int(number), matched.group(2)
            except ValueError:
                return parse_int(number), matched.group(2)

        for drug in DRUGS:
            if drug in line:
                matched = re.search(QUANTIFIER, line)
                try:
                    price = matched.group(1)
                    amount = matched.group(2)
                    unit_price = ''
                    amount_ = split_int(amount)
                    if amount_[1] == '克':
                        price_ = split_int(price)
                        unit_price = f'{price_[0] // amount_[0]}{price_[1]}/{amount_[1]}'
                    drugs.append((price, f'{amount_[0]}{amount_[1]}', drug, unit_price))
                except AttributeError:
                    continue

    def get_payment(line: str, payments: set):
        for payment in PAYMENTS:
            if payment in line:
                payments.add(payment)

    def get_shipping(line: str, shippings: set):
        for shipping in SHIPPINGS:
            if shipping in line:
                shippings.add(shipping)

    contact_infos = set()
    drugs = []
    payments = set()
    # shippings = set()

    line = ''
    while not line.endswith('判决如下：'):
        line = next(lines)

        get_contact_info(line, contact_infos)
        get_drug(line, drugs)
        get_payment(line, payments)
        # get_shipping(line, shippings)

    return contact_infos, drugs, payments


def get_first_accused_judgement(lines: filter) -> (str, list, (str, str), int):
    def parse_prison_term(from_: str, to: str) -> int:
        # --- std ---
        from datetime import datetime
        # --- external ---
        from dateutil import rrule

        from_ = datetime(*parse_date(from_))
        to = datetime(*parse_date(to))
        months = rrule.rrule(rrule.MONTHLY, dtstart=from_, until=to).count()

        return int(months)

    judgement = next(lines)
    infos = iter(judgement.split('，'))

    matched = re.search(r'被告人(.+)犯(.+)', next(infos))
    name = matched.group(1)

    accusations = [matched.group(2)]
    forfeit_type = ''
    forfeit = []
    prison_term = ('', '')
    for info in infos:
        print(info)
        try:
            matched = re.search(r'(罚金|没收财产)(人民币)?(.+)元', info)
            forfeit.append(matched.group(3))
            forfeit_type = matched.group(1)
        except AttributeError:
            try:
                accusations.append(re.search(r'犯(.+罪)', info).group(1))
            except AttributeError:
                try:
                    matched = re.search(r'即自(.+)起至(.+)止', info)
                    prison_term = (matched.group(1), matched.group(2))
                except AttributeError:
                    continue

    if prison_term == ('', ''):
        matched = re.search(r'即自(.+)起至(.+)止', next(lines))
        prison_term = (matched.group(1), matched.group(2))

    return name, accusations, parse_prison_term(*prison_term), sum(map(parse_int, forfeit)), forfeit_type


def parse_doc(path: str):
    lines = read_doc(path)
    case_id = get_case_id(lines)
    print(case_id)
    court = get_court(lines)
    print(court)
    accuseds = get_accuseds(lines)
    print(accuseds)
    youngest_accused = get_youngest_accuseds(accuseds)
    print(youngest_accused)
    contact_infos, drugs, payments = get_detail(lines)
    print(contact_infos, drugs, payments)
    (
        first_accused_name,
        first_accused_accusation,
        first_accused_prison_term,
        first_accused_forfeit,
        first_accused_forfeit_type
    ) = get_first_accused_judgement(lines)
    print(first_accused_name, first_accused_accusation, first_accused_prison_term, first_accused_forfeit, first_accused_forfeit_type)


def test_case():
    lines = read_doc('（2018）浙0281刑初30号.docx')
    case_id = get_case_id(lines)
    print(case_id)
    court = get_court(lines)
    print(court)
    accuseds = get_accuseds(lines)
    print(accuseds)
    youngest_accused = get_youngest_accuseds(accuseds)
    print(youngest_accused)
    contact_infos, drugs, payments = get_detail(lines)
    print(contact_infos, drugs, payments)
    (
        first_accused_name,
        first_accused_accusation,
        first_accused_prison_term,
        first_accused_forfeit,
        first_accused_forfeit_type
    ) = get_first_accused_judgement(lines)
    print(first_accused_name, first_accused_accusation, first_accused_prison_term, first_accused_forfeit, first_accused_forfeit_type)
