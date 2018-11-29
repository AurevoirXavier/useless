from cases import all_cases, parse_doc, test_case

if __name__ == '__main__':
    # test_case('2017年走私、贩卖、运输、制造毒品罪/舟山/（2017）浙0921刑初91号.docx')

    for years in all_cases():
        for locations in years:
            for case in locations:
                parse_doc(case)
                input()
