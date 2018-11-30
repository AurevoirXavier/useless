# --- std ---
from csv import writer
from os import remove, path
from pickle import dump, load

# --- custom ---
from cases import all_cases, parse_doc, test_case

if __name__ == '__main__':
    # test_case('2017年走私、贩卖、运输、制造毒品罪/宁波/（2017）浙0282刑初453号.docx')

    read_cases = set()
    if path.isfile('read_cases'):
        with open('read_cases', 'rb') as f:
            read_cases = load(f)

    for dir_name, year in all_cases():
        csv = f'{dir_name}.csv'
        with open(csv, 'w', encoding='utf-8-sig') as f:
            w = writer(f)
            w.writerow([
                '法院',
                '案号',
                '所有被告',
                '第一被告姓名',
                '第一被告性别',
                '第一被告出生时间',
                '第一被告民族',
                '第一被告教育水平',
                '第一被告职业',
                '第一被告籍贯',
                '最小出生日期',
                '毒品',
                '联系方式',
                '支付方式',
                '运输方式'
            ])

        for location in year:
            for case in location:
                if case in read_cases:
                    continue

                parse_doc(case, save_to_csv=(True, csv))

                read_cases.add(case)
                with open('read_cases', 'wb') as f:
                    dump(read_cases, f)

    remove('read_cases')
