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
            '〇': '0',
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
    from conf import ACCUSED_INFO

    line = next(lines)
    if '原告人' in line:  # skip accuser
        line = next(lines)

    accuseds = []
    while line.startswith('被告人'):
        matched = re.match(ACCUSED_INFO, line)

        accused = {
            'name': matched.group(1).split('（')[0],
            'sexual': matched.group(2).replace('，', ''),
            'birthday': matched.group(3),
            'nation': matched.group(4),
            'education': matched.group(5),
            'occupation': matched.group(6),
            'native_place': re.sub(r'(户籍地|家住|住)', '', matched.group(7))[0:-1]
        }
        accuseds.append(accused)

        line = next(lines)
        if '辩护人' in line:  # skip attorney
            line = next(lines)

    return accuseds


def get_min_birthday(accuseds: list) -> str:
    min_birthday = (0, 0, 0)
    for accused in accuseds:
        birthday = parse_date(accused['birthday'])
        for i in range(3):
            if birthday[i] > min_birthday[i]:
                min_birthday = birthday
            elif birthday[i] < min_birthday[i]:
                break

    return f'{min_birthday[0]}年{min_birthday[1]}月{min_birthday[2]}日'


def get_detail(lines: filter) -> (set, list, set):
    # --- custom ---
    from conf import CONTACT_INFOS, DRUGS, DRUGS_SOURCE, PAYMENTS, QUANTIFIERS, SHIPPINGS

    def get_contact_info(line: str, contact_infos: set):
        for contact_info in CONTACT_INFOS:
            if contact_info in line:
                contact_infos.add(contact_info)

    def get_drug(line: str, drugs: list):
        def split_float(text: str) -> (float, str):
            matched = re.match(r"([一二三四五六七八九十百千万]+|\d+\.\d+|\d+)(.+)", text)
            number = matched.group(1)
            try:
                return float(number), matched.group(2)
            except ValueError:
                return float(parse_int(number)), matched.group(2)

        for drug in DRUGS:
            if drug in line:
                for quantifier in QUANTIFIERS:
                    matched = re.search(quantifier, line)
                    try:
                        if '元' in matched.group(1):
                            price = matched.group(1)
                            amount = matched.group(2)
                        else:
                            price = matched.group(2)
                            amount = matched.group(1)

                        unit_price = ''
                        amount_ = split_float(amount)
                        if amount_[1] == '克':
                            price_ = split_float(price)
                            unit_price = f'{price_[0] // amount_[0]}{price_[1]}/{amount_[1]}'

                        drugs.append((price, f'{amount_[0]}{amount_[1]}', drug, unit_price))
                        break
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
        line = ''.join(next(lines).split())

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

    judgement = ''
    while '犯' not in judgement:
        judgement = next(lines)

    infos = iter(judgement.split('，'))

    matched = re.search(r'被告人(.+)犯(.+)', next(infos))
    name = matched.group(1)
    accusations = [matched.group(2)]

    forfeit_type = ''
    forfeit = []
    prison_term = ('', '')
    for info in infos:
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
    print('案号: ', case_id)
    court = get_court(lines)
    print('法院: ', court)
    accuseds = get_accuseds(lines)
    print('被告人: ',accuseds)
    min_birthday = get_min_birthday(accuseds)
    print('最小出生日期: ', min_birthday)
    contact_infos, drugs, payments = get_detail(lines)
    print('联系方式: ', contact_infos)
    print('毒品: ', drugs)
    print('支付方式: ', payments)
    (
        first_accused_name,
        first_accused_accusation,
        first_accused_prison_term,
        first_accused_forfeit,
        first_accused_forfeit_type
    ) = get_first_accused_judgement(lines)
    print('第一被告人: ', first_accused_name, first_accused_accusation, first_accused_prison_term, first_accused_forfeit, first_accused_forfeit_type)


def test_case(path: str):
    lines = read_doc(path)
    case_id = get_case_id(lines)
    # print('案号: ', case_id)
    court = get_court(lines)
    # print('法院: ', court)
    accuseds = get_accuseds(lines)
    # print('被告人: ',accuseds)
    min_birthday = get_min_birthday(accuseds)
    # print('最小出生日期: ', min_birthday)
    contact_infos, drugs, payments = get_detail(lines)
    # print('联系方式: ', contact_infos)
    # print('毒品: ', drugs)
    # print('支付方式: ', payments)
    (
        first_accused_name,
        first_accused_accusation,
        first_accused_prison_term,
        first_accused_forfeit,
        first_accused_forfeit_type
    ) = get_first_accused_judgement(lines)
    print('第一被告人: ', first_accused_name, first_accused_accusation, first_accused_prison_term, first_accused_forfeit, first_accused_forfeit_type)
    input()
