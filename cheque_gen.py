import os
import random
import string
import xml.etree.ElementTree as ET
from xml.dom import minidom
from xmlschema import XMLSchema
import requests  

SCHEMA = "cheque.xsd"
OUT_DIR = "cheque"
ROOT_TAG = "Cheque"

UPLOAD_URL = "http://localhost:8080"   
SEND_TO_SERVER = True                

INN_POOL = [
"7805145876",
"7810270262",
"7818011277",
"7814355894",
"7806126770",
"7813118812",
"7838338256",
"5904209767",
"4217030520",
"3702666196"
]

EAN_POOL = [
"8584005040985",
"4007817304679",
"4041485023685",
"4620000630227",
"4041485000105",
"4041485138129",
"4005401854180",
"4680002181295",
"4017773002472",
"4607168072120"
]

FIXED_ATTRS = {
    "@name": "ООО «Ромашка»", #)))
}

DT_REGEX = r'[0-3][0-9][0-1][0-9][0-9]{2}[0-2][0-9][0-5][0-9]'
BARCODE_REGEX = r'\d\dN\w{20}\d[0-1]\d[0-3]\d{10}\w{31}'
PRICE_REGEX = r'-?\d+\.\d{1,2}'
VOLUME_REGEX = r'\d+\.?\d{0,4}'

schema = XMLSchema(SCHEMA)

def random_kpp():
    return ''.join(random.choices('0123456789', k=9))

def random_adress():
    length = random.randint(20, 100)
    base = [random.choice('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ') for _ in range(length - 2)]
    positions = sorted(random.sample(range(length), 2))
    result = []
    j = 0 
    for i in range(length):
        if j < 2 and i == positions[j]:
            result.append(' ')
            j += 1
        else:
            result.append(base.pop(0))
    return ''.join(result)

def random_kassa() -> str:
    length = random.randint(6, 12)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.choices(chars, k=length))

def random_date():
    chars = []
    chars.append(random.choice('0123'))
    chars.append(random.choice('0123456789'))
    chars.append(random.choice('01'))
    chars.append(random.choice('0123456789'))
    chars.append(random.choice('0123456789'))
    chars.append(random.choice('0123456789'))
    chars.append(random.choice('012'))
    chars.append(random.choice('0123456789'))
    chars.append(random.choice('012345'))
    chars.append(random.choice('0123456789'))
    return ''.join(chars)

def random_barcode():
    chars_w = string.ascii_letters + string.digits + '_'

    part1 = ''.join(random.choices(string.digits, k=2))       # \d\d
    part2 = 'N'                                               # N
    part3 = ''.join(random.choices(chars_w, k=20))            # \w{20}
    part4 = random.choice(string.digits)                      # \d
    part5 = random.choice('01')                               # [0-1]
    part6 = random.choice(string.digits)                      # \d
    part7 = random.choice('0123')                             # [0-3]
    part8 = ''.join(random.choices(string.digits, k=10))      # \d{10}
    part9 = ''.join(random.choices(chars_w, k=31))            # \w{31}

    return f"{part1}{part2}{part3}{part4}{part5}{part6}{part7}{part8}{part9}"

def random_ean():
    return random.choice(EAN_POOL)

def random_inn():
    return random.choice(INN_POOL)

def random_price():
    sign = '-' if random.random() < 0.5 else ''
    value = random.uniform(100.0, 1000.0)
    return f"{sign}{value:.2f}"

def random_volume():
    # Минимум 0.1, максимум 3.0, шаг 0.05 -> количество шагов: (3.0 - 0.1) / 0.05 + 1 = 2.9/0.05 + 1 = 58 + 1 = 59
    steps = random.randint(0, 58)
    value = 0.1 + steps * 0.05
    return f"{value:.4f}"

def make_bottles(n=None):
    if n is None:
        n = random.randint(1, 6)
    bottles = []
    seen = set()
    for _ in range(n):
        while True:
            bc = random_barcode()
            if bc not in seen:
                seen.add(bc)
                break
        bottles.append({
            "@price": random_price(),
            "@barcode": bc,
            "@ean": random_ean(),
            "@volume": random_volume()
        })
    return bottles

def build_cheque():
    data = dict(FIXED_ATTRS)
    data["@inn"] = random_inn()
    data["@kpp"] = random_kpp()
    data["@address"] = random_adress()
    data["@shift"] = random.randint(1, 100)
    data["@number"] = random.randint(1000, 9999)
    data["@datetime"] = random_date()
    data["Bottle"] = make_bottles()
    data["@kassa"] = random_kassa()
    return data

def format_xml(elem):
    rough = ET.tostring(elem, encoding='utf-8')
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="UTF-8")

def upload_file(filepath, url):
    try:
        with open(filepath, 'rb') as f:
            files = {'xml_file': (os.path.basename(filepath), f, 'application/xml')}
            response = requests.post(url, files=files, timeout=5)
        if response.status_code == 200:
            print(f"  -> Отправлен успешно на {url}")
            return True
        else:
            print(f"  -> Сервер вернул {response.status_code}: {response.text[:100]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  -> Ошибка отправки: {e}")
        return False

def main():
    try:
        n = int(input("Сколько чеков сгенерировать: "))
    except ValueError:
        print("Нужно число. Выход.")
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    for i in range(1, n + 1):
        try:
            xml_elem = schema.encode(build_cheque(), path=ROOT_TAG, validation='strict')
            xml_str = format_xml(xml_elem)
            fname = os.path.join(OUT_DIR, f"cheque_{i:04d}.xml")
            with open(fname, 'wb') as f:
                f.write(xml_str)
            print(f"Создан: {fname}")

            if SEND_TO_SERVER and UPLOAD_URL:
                upload_file(fname, UPLOAD_URL)

        except Exception as e:
            print(f"Ошибка при создании чека {i}: {e}")

if __name__ == "__main__":
    main()