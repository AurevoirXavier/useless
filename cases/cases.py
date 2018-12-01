# --- std ---
import re


def all_cases(path: str) -> map:
    # --- std ---
    from os import listdir

    def is_dir(d: str) -> bool:
        # --- std ---
        from os.path import isdir

        return not d.startswith('.') and isdir(d) and d != '__pycache__'

    def is_file(f: str) -> bool:
        # --- std ---
        from os.path import isfile

        return not f.startswith('.') and isfile(f)

    def filter_dir(fn: callable, parent: str) -> filter:
        return filter(fn, map(lambda descendant: f'{parent}/{descendant}', listdir(parent)))

    return map(lambda d: (d, map(lambda f: filter_dir(is_file, f), filter_dir(is_dir, d))), filter(is_dir, listdir(path)))


def read_doc(f: str) -> filter:
    # --- std ---
    from os import remove, path
    from subprocess import DEVNULL, call
    # --- external ---
    from docx import Document

    def strip_doc(doc: list) -> filter:
        # --- std ---
        from unicodedata import normalize

        return filter(lambda _: _, map(lambda line: normalize('NFKC', ''.join(line.text.split())), doc))

    def convert_doc(doc: str) -> str:
        call(['soffice', '--headless', '--convert-to', 'docx', doc, '--outdir', f'{path.dirname(doc)}'], stdout=DEVNULL)

        if path.isfile(f'{doc}x'):
            remove(doc)
        return f'{doc}x'

    if f.endswith('DOC'):
        f = f'{f[:-3]}doc'

    if f.endswith('doc'):
        f = convert_doc(f)

    print(f)
    if f.endswith('docx'):
        return strip_doc(Document(f).paragraphs)
    else:
        raise ValueError


def skip_special_type(special_type: str) -> bool:
    if special_type == '暂予监外执行决定书':
        return True
    else:
        return False


def get_court(lines: filter) -> str:
    court = ''
    while not court.endswith('人民法院'):
        court = next(lines)

    court = re.match(r'(.+)人民法院', court).group(1)
    court = re.sub(r'.+省', '', court)

    return court


def parse_float(number: str) -> float:
    def parse_int(x: str) -> str:
        return {
            '0': '0',
            '○': '0',
            '〇': '0',
            '零': '0',
            '一': '1',
            '二': '2',
            '两': '2',
            '三': '3',
            '四': '4',
            '五': '5',
            '六': '6',
            '七': '7',
            '八': '8',
            '九': '9'
        }.get(x, '')

    def parse_quantifier(quantifier: str) -> float:
        return {
            '十': 10.,
            '百': 100.,
            '千': 1000.,
            '万': 10000.
        }.get(quantifier, 1.)

    try:
        return float(number)
    except TypeError:
        return 0.
    except ValueError:
        start_with_ten = {
            '十': 10.,
            '十一': 11.,
            '十二': 12.,
            '十三': 13.,
            '十四': 14.,
            '十五': 15.,
            '十六': 16.,
            '十七': 17.,
            '十八': 18.,
            '十九': 19.,
            '十万': 100000.,
        }
        if number in start_with_ten:
            return start_with_ten[number]

        matched = re.match(r'(\d+\.\d+|\d+)([十百千万])', number)
        if matched is not None:
            return float(matched.group(1)) * parse_quantifier(matched.group(2))

        return parse_quantifier(number[-1]) * float((''.join(map(parse_int, number))))


def parse_date(date: str) -> (int, int, int):
    matched = re.search(r'(.{4})年(.{1,})月([一二三四五六七八九十\d]{1,})日?', date)
    try:
        return int(matched.group(1)), int(matched.group(2)), int(matched.group(3))
    except ValueError:
        return int(parse_float(matched.group(1))), int(parse_float(matched.group(2))), int(parse_float(matched.group(3)))


def get_accuseds(lines: filter) -> list:
    from conf import EDUCATIONS, RESIDENCE

    next(lines)  # skip court
    line = next(lines)
    if '原告人' in line:  # skip accuser
        line = next(lines)

    accuseds = []
    while line.startswith('被告人'):
        for accused in accuseds:
            if accused['name'] in line:
                return accuseds

        name = re.match(r'被告人(.+?)(?:\(.+?\))?,', line).group(1)
        #  fuck special doc
        if ',' in name:
            raise ValueError

        sex = re.search(r'([男女]),', line)
        sex = '' if sex is None else sex.group(1)
        nation = re.search(r',([^,]+?族),', line)
        nation = '' if nation is None else nation.group(1)
        birthday = re.search(r'([l\d]{4})年([l\d]{1,2})月([l\d]{1,2})日?[出生于]?', line)

        for pattern in [
            rf'(?:.+人,|.+人.+族,)?(?:.*?({EDUCATIONS}).*?,)?(?:.+人.+族,)?(?:([^\d家住户籍所在地为]+?),)?(?:.+人,)?(?:{RESIDENCE})([^。]+?[省县市镇村].+?)?[(;,。]',
            rf'(?:.+人,|.+人.+族,)?(?:.*?({EDUCATIONS}).*?,)?(?:.+人.+族,)?(?:([^\d家住户籍所在地为]+?),)?(?:.+人,)?([^。]+?[省县市镇村].+?)?[(;,。]'
        ]:
            matched = re.search(pattern, line)
            if matched is not None:
                break

        accuseds.append({
            'name': name,
            'sex': sex,
            #                                                            fuck l990
            'birthday': '' if birthday is None else [int(birthday.replace('l', '1')) for birthday in birthday.groups()],
            'nation': nation,
            'education': '' if matched.group(1) is None else matched.group(1),
            'occupation': '' if matched.group(2) is None else matched.group(2),
            'native_place': '' if matched.group(3) is None else matched.group(3)
        })

        line = next(lines)
        if '辩护人' in line:  # skip attorney
            line = next(lines)

    return accuseds


def get_min_birthday(accuseds: list) -> str:
    min_birthday = (0, 0, 0)
    for accused in accuseds:
        birthday = accused['birthday']
        for i in range(3):
            if birthday[i] > min_birthday[i]:
                min_birthday = birthday
            elif birthday[i] < min_birthday[i]:
                break

    return f'{min_birthday[0]}年{min_birthday[1]}月{min_birthday[2]}日'


def get_detail(lines: filter) -> (set, dict, set, set):
    # --- custom ---
    from conf import CONTACT_INFOS, DRUGS, DRUGS_SOURCE, PAYMENTS, QUANTIFIERS, SHIPPINGS

    def get_contact_info(line: str, contact_infos: set):
        for contact_info in CONTACT_INFOS:
            if contact_info in line:
                contact_infos.add(contact_info)

    def get_drug(line: str, drugs: dict):
        def split_float(text: str) -> (float, str):
            matched = re.match(r"([一二三四五六七八九十百千万]+|\d+\.\d+|\d+)(.+)", text)
            number = matched.group(1)
            try:
                return float(number), matched.group(2)
            except ValueError:
                return parse_float(number), matched.group(2)

        for drug in DRUGS:
            if drug in line:
                if drug not in drugs:
                    drugs[drug] = set()

                matched = re.search(r'(\d+\.\d+|\d+)克,每克(d+)元', line)
                if matched is None:
                    for quantifier in QUANTIFIERS:
                        matched = re.search(quantifier, line)
                        if matched is None:
                            continue

                        if '元' in matched.group(1):
                            price = matched.group(1)
                            amount = matched.group(2)
                        else:
                            price = matched.group(2)
                            amount = matched.group(1)

                        unit_price = ''
                        amount_ = split_float(amount)
                        if amount_[1] in '克粒':
                            price_ = split_float(price)
                            unit_price = round(price_[0] / amount_[0], 1)
                            #  wrong data
                            if unit_price < 100.:
                                continue
                            unit_price = f'{unit_price}{price_[1]}/{amount_[1]}'

                        return drugs[drug].add((str(price), f'{amount_[0]}{amount_[1]}', unit_price))
                else:
                    amount = float(matched.group(1))
                    price_per_gram = float(matched.group(2))
                    return drugs[drug].add((str(amount * price_per_gram), f'{amount}克', f'{price_per_gram}元/克'))

    def get_payment(line: str, payments: set):
        for payment in PAYMENTS:
            if payment in line:
                return payments.add(payment)

    def get_shipping(line: str, shippings: set):
        for shipping in SHIPPINGS:
            if shipping in line:
                return shippings.add(shipping)

    contact_infos = set()
    drugs = {}
    payments = set()
    shippings = set()

    line = ''
    while not line.endswith('判决如下:'):
        try:
            line = next(lines)
        except StopIteration:
            return set(), {}, set(), set()

        get_contact_info(line, contact_infos)
        get_drug(line, drugs)
        get_payment(line, payments)
        get_shipping(line, shippings)

    return contact_infos, drugs, payments, shippings


def get_first_accused_judgement(lines: filter, accuseds: list) -> (list, str, str, int):
    # --- custom ---
    from conf import PRISON_TERM

    def parse_prison_term(from_: str, to: str) -> int:
        # --- std ---
        from datetime import datetime
        # --- external ---
        from dateutil import rrule

        try:
            from_ = datetime(*parse_date(from_))

            year, month, day = parse_date(to)
            #  fuck 11/31
            if day == 31:
                day -= 1
            to = datetime(year, month, day)
        except ValueError:
            raise ValueError
        months = rrule.rrule(rrule.MONTHLY, dtstart=from_, until=to).count()

        return int(months)

    judgement = ''
    while '被告人' not in judgement or '犯' not in judgement:
        try:
            judgement = next(lines)
        except StopIteration:
            return [], '', '', 0

    infos = iter(judgement.split(','))

    info = next(infos)
    matched = re.search(r'被告人.+?犯(.+?罪)', info)
    if matched is None:
        for accused in accuseds:
            if accused['name'] in info:
                name = accused['name']
                accusations = [info.split(name)[1]]
                break
    else:
        accusations = [matched.group(1)]

    forfeit_type = ''
    forfeit = []
    prison_term = ('', '')
    reserve_prison_term = ('', '')

    for info in infos:
        #                                                    fuck 人民元
        matched_forfeit = re.search(r'(罚金|没收财产|没收个人财产)(?:计?人民[元币]为?)?(.+?)元', info)
        matched_accusation = re.search(r'犯(.+?罪)', info)
        matched_prison_term = re.search(PRISON_TERM, info)
        matched_reserve_prison_term = re.search(r'判处.+[刑役制](?:(.+?)年)?(?:(.+?)个月)?', info)

        if matched_forfeit is not None:
            forfeit_type = matched_forfeit.group(1)
            forfeit.append(matched_forfeit.group(2))
        elif matched_accusation is not None:
            accusations.append(matched_accusation.group(1))
        elif matched_prison_term is not None:
            try:
                prison_term = parse_prison_term(matched_prison_term.group(1), matched_prison_term.group(2))
            except ValueError:
                ()

        if matched_reserve_prison_term is not None:
            reserve_prison_term = (matched_reserve_prison_term.group(1), matched_reserve_prison_term.group(2))

    if prison_term == ('', ''):
        matched = re.search(PRISON_TERM, next(lines))
        if matched is None:
            prison_term = 0 if reserve_prison_term == ('', '') \
                else int(parse_float(reserve_prison_term[0])) * 12 + int(parse_float(reserve_prison_term[1]))
        else:
            prison_term = 0 if matched.groups() == ('年月日', '年月日') \
                else parse_prison_term(matched.group(1), matched.group(2))

    return accusations, prison_term, sum(map(parse_float, forfeit)), forfeit_type


def parse_doc(path: str, save_to_csv: (bool, str, int)):
    try:
        lines = read_doc(path)
    except ValueError:
        return

    try:
        court = get_court(lines)
        print('法院: ', court)
    except StopIteration:
        return

    if skip_special_type(next(lines)):
        return

    case_id = next(lines)
    print('案号: ', case_id)

    if case_id == '(简易程序独任审判案件专用)':
        return

    try:
        accuseds = get_accuseds(lines)
        print('被告人: ', accuseds)
    except ValueError:
        return

    min_birthday = get_min_birthday(accuseds)
    print('最小出生日期: ', min_birthday)

    contact_infos, drugs, payments, shippings = get_detail(lines)
    print('联系方式: ', contact_infos)
    print('毒品: ', drugs)
    print('支付方式: ', payments)
    print('运输方式: ', shippings)

    first_accused = accuseds[0] if accuseds else {}
    (
        first_accused_accusation,
        first_accused_prison_term,
        first_accused_forfeit,
        first_accused_forfeit_type
    ) = get_first_accused_judgement(lines, accuseds)
    print('第一被告人: ', first_accused, first_accused_accusation, first_accused_prison_term, first_accused_forfeit, first_accused_forfeit_type)

    if save_to_csv[0]:
        # --- std ---
        from csv import writer

        def parse_key(key: str) -> str:
            return {
                'name': '姓名',
                'sex': '性别',
                'birthday': '出生时间',
                'nation': '民族',
                'education': '文化水平',
                'occupation': '职业',
                'native_place': '籍贯'
            }[key]

        with open(save_to_csv[1], 'a', encoding='utf-8-sig', newline='') as f:
            w = writer(f)

            if save_to_csv[2] == 1:
                w.writerow([
                    court,
                    case_id,
                    ', '.join(map(lambda accused: accused['name'], accuseds)),
                    first_accused.get('name', ''),
                    first_accused.get('sex', ''),
                    f'{first_accused["birthday"][0]}年{first_accused["birthday"][1]}月{first_accused["birthday"][2]}日' if 'birthday' in first_accused else '',
                    first_accused.get('nation', ''),
                    first_accused.get('education', ''),
                    first_accused.get('occupation', ''),
                    first_accused.get('native_place', ''),
                    min_birthday,
                    '。'.join(map(lambda drug: f'{drug[0]}: {"; ".join(map(lambda detail: ", ".join(detail), drug[1]))}', drugs.items())),
                    ', '.join(contact_infos),
                    ', '.join(payments),
                    ', '.join(shippings)
                ])
            else:
                w.writerow([
                    court,
                    case_id,
                    '。'.join(map(lambda accused: ', '.join(map(lambda detail: f'{parse_key(detail[0])}: {detail[1]}', accused.items())), accuseds))
                ])


def test_case(path: str):
    try:
        lines = read_doc(path)
    except ValueError:
        return

    try:
        court = get_court(lines)
        print('法院: ', court)
    except StopIteration:
        return

    if skip_special_type(next(lines)):
        return

    case_id = next(lines)
    print('案号: ', case_id)
    #  fuck special doc
    if case_id == '(简易程序独任审判案件专用)':
        return

    try:
        accuseds = get_accuseds(lines)
        print('被告人: ', accuseds)
    except ValueError:
        return

    min_birthday = get_min_birthday(accuseds)
    print('最小出生日期: ', min_birthday)

    contact_infos, drugs, payments, shipping = get_detail(lines)
    print('联系方式: ', contact_infos)
    print('毒品: ', drugs)
    print('支付方式: ', payments)
    print('运输方式: ', shipping)

    (
        first_accused_name,
        first_accused_accusation,
        first_accused_prison_term,
        first_accused_forfeit,
        first_accused_forfeit_type
    ) = get_first_accused_judgement(lines, accuseds)
    print('第一被告人: ', first_accused_name, first_accused_accusation, first_accused_prison_term, first_accused_forfeit, first_accused_forfeit_type)
    input()
