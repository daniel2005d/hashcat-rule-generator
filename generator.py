import itertools
import string
import subprocess
from uuid import uuid4
from os import path
import argparse
import platform

parser = argparse.ArgumentParser()

parser.add_argument("-o",'--output', help='Output file rule', required=True)
parser.add_argument("-w",'--wordlist', help='Diccionary', required=True)
parser.add_argument("-n",'--numbers',action='append', help='Add especial numbers. Format: (1900-2000) o (2010,2012,2020,2021)')
parser.add_argument("-d",'--date',action='append', help='Special dates. Format: DDMMYYYY')
parser.add_argument("-nl",'--no-leet',action='store_false', help='Special dates. Format: DDMMYYYY')

args = parser.parse_args()

file_rule = args.output
file_words = args.wordlist
numbers = args.numbers
special_dates = args.date
no_leet = args.no_leet


base_folder = path.dirname(file_words)
os_name = platform.system()
new_wordlist = None

if os_name == "Windows":
    new_wordlist = f'{base_folder}\\{str(uuid4())}.lst'
else:
    new_wordlist = f'{base_folder}/{str(uuid4())}.lst'
max_length = 0

with open(file_words, "r", encoding="utf-8") as f:
    max_length = max(len(line.strip()) for line in f)


special_chars = ["!","@","#","$","%","&","*",".",",","?","+"]
leet = {
    "a":["4","@"],
    "e":["3"],
    "i":["l","1","|"],
    "o":["0"],
    "t":["7"],
    "5":["s"],
    "g":["9"],
    "z":["2"]
}

default_rules = ["l","u"]


def combine_dates():
    combinations = set()
    days = sorted({date[:2] for date in special_dates})
    months = sorted({date[2:4] for date in special_dates})
    years = sorted({date[4:8] for date in special_dates})
    i = itertools.product(days, months)
    for d,m in i:
        combinations.add(d+m)
        combinations.add(m+d)

    return sorted(combinations)

def add_specialchars(line=None):
    if line:
        for c in special_chars:
            write_rule(f'${c}{line}', min_word)
            write_rule(f'{line}${c}', min_word)
    
    for c in itertools.permutations(special_chars,2):
        combinations = ''
        for iter in c:
            combinations+=f'${iter}'
        
        write_rule(combinations, min_word)

def add_dates(number):
    line = ''
    values_added = []
    if number not in values_added:
        for r in number:
            line += f'${r}'
            values_added.append(number)
            
        if line:
            return line
    
def toggle_letter():
    for t in range(max_length):
        write_rule(f'T{t}')
        for l in leet:
            for v in leet[l]:
                write_rule(f's{l}{v}T{t}')

def add_numbers():
    for n in string.digits:
        write_rule(f'${n}')
        for c in special_chars:
            write_rule(f'${c}${n}')
            write_rule(f'${n}${c}')


def write_rule(line:str):
    

    if line not in lines_saved:
        rule.write(f'{line}\n')
        lines_saved.append(line)
        if len(lines_saved) % 20 == 0:
            rule.flush()

def additional_numbers(list_numbers):
    for numbers in list_numbers:
        add_custom_number(numbers)

def write_letter(letter):
    line = ''
    for l in letter:
        line+=f'${l}'
    
    write_rule(line)
    

def add_custom_number(numbers):
    range_numbers = set()
    if ',' in numbers:
        fragments = numbers.split(',')
        for n in fragments:
            range_numbers.add(n)
    elif '-' in numbers:
        fragments = numbers.split("-")
        n1 = fragments[0]
        n2 = fragments[1]
        for n in range(int(n1),int(n2)+1):
            range_numbers.add(str(n))
    elif numbers:
        range_numbers.add(numbers)
        
    for n in range_numbers:
        write_letter(n)
        
        for num,char in itertools.product(range_numbers, special_chars):
            write_letter(num+char)
        

        for char, num in itertools.product(special_chars, range_numbers):
            write_letter(char + num)

        for izq, num, der in itertools.product(special_chars, range_numbers, special_chars):
            write_letter(izq + num + der)
    

"""
    Se adcionan las fechas especificadas
"""
def add_special_dates():
    dates = combine_dates()
    for d in dates:
        v1 = d[:2]
        v2 = d[2:4]
        linev1 = add_dates(v1)
        linev2 = add_dates(v2)
        write_rule(linev1, min_word)
        write_rule(linev2, min_word)
        write_rule(linev1+linev2, min_word)
        add_specialchars(linev1)
        add_specialchars(linev2)
        add_specialchars(linev1+linev2)

def add_leet():
    ## L33t
    for l in leet:
        for v in leet[l]:
            write_rule(f's{l}{v}')

def recreate_wordlist(wordlist):
    rule.flush()
    
    process = subprocess.Popen(["hashcat",wordlist,"-r", file_rule, "--stdout"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE  ,
                                text=True,
                                startupinfo=None)
    stdout, stderr = process.communicate()
    if stderr:
        print(f"[!ERROR] {stderr} ")
    elif stdout:
        
        with open(new_wordlist, 'w', encoding='utf-8') as f:
            for line in list(set(stdout.split())):
                f.write(line+'\n')

        return new_wordlist

lines_saved = []
rule = open(file_rule, 'w')

## Default Rules
for default in default_rules:
    write_rule(default)

toggle_letter()
if no_leet:
    add_leet()

wordlist = recreate_wordlist(file_words)

if wordlist:
    if special_dates:
        add_special_dates()
    # Numeros 0-9
    add_numbers()
    # Numeros adicionales especificados
    additional_numbers(numbers)
    rule.close()


    print(f"[*] hashcat {new_wordlist} hashes.txt -r {file_rule}")
    print(f"[*] hashcat {new_wordlist} -r {file_rule} --stdout")
