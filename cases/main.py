# --- std ---
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

    for year in all_cases():
        for location in year:
            for case in location:
                if case in read_cases:
                    continue

                parse_doc(case)

                read_cases.add(case)
                with open('read_cases', 'wb') as f:
                    dump(read_cases, f)

    remove('read_cases')
