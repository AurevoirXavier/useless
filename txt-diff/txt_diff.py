# --- std ---
from os import listdir, mkdir, rename
from os.path import isdir

check_name = True
fields = [0 for _ in range(15)]
fields_name = [
    'name', 'phone', 'mail',
    'duration1', 'school1', 'department1', 'major1',
    'duration2', 'school2', 'department2', 'major2',
    'duration3', 'school3', 'department3', 'major3'
]

if not isdir('error'):
    mkdir('error')
for name in fields_name:
    path = f'error/{name}'
    if not isdir(path):
        mkdir(path)

for f in listdir(''):
    if f.endswith('_Groundtruth.txt'):
        num, _ = f.split('_Groundtruth.txt')

        with open(f, 'r') as gt_f:
            with open(num, 'r') as cmp_f:
                gt_text = gt_f.read().strip().splitlines()
                cmp_text = cmp_f.read().strip().splitlines()

                for i in range(15):
                    if gt_text[i] == cmp_text[i]:
                        fields[i] += 1
                    else:
                        rename(f'cmp/{num}.jpg', f'error/{fields_name[i]}/{num}_{gt_text[i]}_{cmp_text[i]}.jpg')

# with open('cmp.txt', 'r') as f:
#     data = ''
#     while True:
#         line = f.readline()
#
#         if check_name:
#             if line.isspace():
#                 check_name = True
#             else:
#                 num = line.strip()[-8:-4]
#                 check_name = False
#
#             continue
#
#         if (line.isspace() or not line) and num:
#             with open(f'cmp/{num}.txt', 'r') as cmp_f:
#                 data = data.strip().splitlines()
#                 cmp_data = cmp_f.read().strip().splitlines()
#
#                 for i in range(15):
#                     if data[i] == cmp_data[i]:
#                         fields[i] += 1
#                     else:
#                         copyfile(f'cmp/{num}.jpg', f'error/{fields_name[i]}/{num}_{data[i]}_{cmp_data[i]}.jpg')
#
#             check_name = True
#             data = ''
#
#             continue
#
#         if not line:
#             break
#
#         data += line
#
# for k, v in zip(fields_name, fields):
#     print(f'{k}: {v}')
