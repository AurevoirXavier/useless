from cases import all_cases, parse_doc, test_case

if __name__ == '__main__':
    # test_case()

    for years in all_cases():
        for locations in years:
            for case in locations:
                parse_doc(case)
