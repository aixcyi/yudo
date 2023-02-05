import re
from json import load as json_load

import click

from core.click_chore import Regex

code_detail = """
  {p}-{c}-{k}-{t}-{n}
   │  │  │   │   └─⫸ {town}
   │  │  │   └─⫸ {township}
   │  │  └─⫸ {county}
   │  └─⫸ {city}
   └─⫸ {province}
 """


@click.command('adc')
@click.option('-d', '--detail', 'code', metavar='CODE', help='查询某个区划代码的详细信息。')
@click.option('-p', '--province', 'provinces', multiple=True, help='按省级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-c', '--city', 'cities', multiple=True, help='按市级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-k', '--county', 'counties', multiple=True, help='按县级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-t', '--township', 'townships', multiple=True, help='按乡级代码(三位数字)筛选区划代码。可填多个。')
@click.option('-n', '--town', 'towns', multiple=True, help='按镇级代码(三位数字)筛选区划代码。可填多个。')
@click.option('-r', '--regex', type=Regex(), help='使用正则表达式筛选划代码。')
@click.option('-T', '--title', help='按名称筛选区划。')
@click.option('--purify', is_flag=True, help='不输出区划代码对应的名称。')
@click.help_option('-h', '--help')
def get_adcode(
        code: str, provinces, cities, counties, townships, towns, regex, title, purify,
):
    """查询某个或列出指定条件下的行政区划代码（Area Division Code）。"""
    with open(r'./code2022.json', 'r', encoding='UTF-8') as f:
        ad_codes = json_load(f)
    if code:
        code = code.ljust(12, '0')[:12]
        print(code_detail.format(
            province=ad_codes.get(f'{code[:2]:012s}', '?'),
            city=ad_codes.get(f'{code[:4]:012s}', '?'),
            county=ad_codes.get(f'{code[:6]:012s}', '?'),
            township=ad_codes.get(f'{code[:9]:012s}', '?'),
            town=ad_codes.get(code, '?'),
            p=code[:2], c=code[2:4], k=code[4:6], t=code[6:9], n=code[9:],
        ))
        return
    codes = ((c, n if n.__class__ is str else n['name']) for c, n in ad_codes.items())
    codes = ((c, n) for c, n in codes if c[0:2] in provinces) if provinces else codes
    codes = ((c, n) for c, n in codes if c[2:4] in cities) if cities else codes
    codes = ((c, n) for c, n in codes if c[4:6] in counties) if counties else codes
    codes = ((c, n) for c, n in codes if c[6:9] in townships) if townships else codes
    codes = ((c, n) for c, n in codes if c[9:12] in towns) if towns else codes
    codes = ((c, n) for c, n in codes if re.fullmatch(regex, c)) if regex else codes
    codes = ((c, n) for c, n in codes if n.find(title)) if title else codes
    if purify:
        print('\n'.join(c for c, _ in codes))
        return
    print('\n'.join(f'{c} {n}' for c, n in codes))
