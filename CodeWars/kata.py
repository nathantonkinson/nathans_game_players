import math

def find_quarter_notes(time_signature):
    data = time_signature.split("/")
    if len(data) != 2:
        return None
    try:
        n = int(data[0])
        d = int(data[1])
    except:
        return None
    #valid denominators are powers of 2
    if (d & (d-1) != 0) or d == 0: #bitwise AND (requires both bits be 1)
        return None
    quarter_notes = math.floor(n/(d/4))
    return quarter_notes

sample_test_cases = [
    ('Standard time signatures', [
        ('4/4',   4),
        ('3/4',   3),
    ]),
    ('Eight-note denominators', [
        ('6/8',   3),
        ('9/8',   4),
    ]),
    ('Very small values', [
        ('1/8',   0),
        ('1/16',  0),
    ]),
    ('Invalid denominators', [
        ('9/0',  None),
        ('7/3',  None),
        ('6/5',  None),
        ('5/6',  None),
        ('3/7',  None),
        ('0/9',  None),
    ]),
    ('Valid sub 4 denominators', [
        ('7/1',  28),
        ('6/2',  12),
    ]),
]

def test_it():
    for set in sample_test_cases:
        for test in set[1]:
            if find_quarter_notes(test[0]) != test[1]:
                print("Failed", test)
            else:
                print("Passed", test)

test_it()
            

# print(find_quarter_notes('4/4'))
