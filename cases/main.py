# --- std ---
from os.path import isfile
from pickle import dump, load

# --- custom ---
from cases import all_cases, parse_doc, test_case

if __name__ == '__main__':
    test_case('2017年走私、贩卖、运输、制造毒品罪/衢州/（2016）浙0802刑初00165号.docx')

    read_cases = set()
    if isfile('read_cases'):
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
