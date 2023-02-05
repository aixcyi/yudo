import re

import click
from json import load as json_load

from core.click_chore import Regex


@click.command('adc')
@click.option('-d', '--detail', 'code', metavar='CODE', help='查询某个区划代码的详细信息。')
@click.option('-p', '--province', 'provinces', multiple=True, help='按省级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-c', '--city', 'cities', multiple=True, help='按市级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-u', '--county', 'counties', multiple=True, help='按县级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-t', '--township', 'townships', multiple=True, help='按乡级代码(三位数字)筛选区划代码。可填多个。')
@click.option('-r', '--regex', type=Regex(), help='使用正则表达式筛选划代码。')
@click.option('--purify', is_flag=True, help='不输出区划代码对应的名称。')
@click.help_option('-h', '--help')
def get_adcode(
        code: str, provinces, cities, counties, townships, regex, purify,
):
    """查询某个或列出指定条件下的行政区划代码（Area Division Code）。"""
    with open(r'./code2022.json', 'r', encoding='UTF-8') as f:
        ad_codes = json_load(f)
    if code:
        code = code.ljust(12, '0')[:12]
        province = ad_codes[p] if (p := f'{code[:2]:012s}') and p in ad_codes else '?'
        city = ad_codes[c] if (c := f'{code[:4]:012s}') and c in ad_codes else '?'
        county = ad_codes[t] if (t := f'{code[:6]:012s}') and t in ad_codes else '?'
        country = ad_codes[y] if (y := f'{code[:9]:012s}') and y in ad_codes else '?'
        township = ad_codes[code] if code and code in ad_codes else '?'
        print(f'详细信息：\n  {province}({p[:6]}) {city}({c[:6]}) {county}({t[:6]}) {country}({y}) {township}({code})')
        return
    codes = ((c, n if n.__class__ is str else n['name']) for c, n in ad_codes.items())
    codes = ((c, n) for c, n in codes if c[0:2] in provinces) if provinces else codes
    codes = ((c, n) for c, n in codes if c[2:4] in cities) if cities else codes
    codes = ((c, n) for c, n in codes if c[4:6] in counties) if counties else codes
    codes = ((c, n) for c, n in codes if c[6:9] in townships) if townships else codes
    codes = ((c, n) for c, n in codes if re.fullmatch(regex, c)) if regex else codes
    if purify:
        print('\n'.join(c for c, _ in codes))
        return
    print('\n'.join(f'{c} {n}' for c, n in codes))
