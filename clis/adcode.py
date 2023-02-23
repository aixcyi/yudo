import re
from json import load as json_load
from pathlib import Path

import click

from core.click_chore import Regex

code_detail = """
  {p}-{c}-{k}-{t}-{o}
   │  │  │   │   └─⫸ {town}
   │  │  │   └─⫸ {township}
   │  │  └─⫸ {county}
   │  └─⫸ {city}
   └─⫸ {province}
"""


def lazy_load():
    # 数据来源：http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2022/index.html
    path = Path(__file__).parent.parent / 'code2022.json'
    with open(path, 'r', encoding='UTF-8') as f:
        return json_load(f)


def search_code(a, b, _code, codes_map):
    """
    搜索区划代码。

    比如搜索某个省所有市区时，
     省的代码必须相同 --> code[:b] == _code[:b]，
     市的代码不能为0 --> code[a:b] != '0'*(b-a)，
     县乡镇的代码必须为0 --> code[b:] == '0'*(12-b)。

    :param a: 搜索位置的起点。
    :param b: 搜索位置的终点。
    :param _code: 搜索的区划代码。
    :param codes_map: 所有区划代码。
    :return: 符合条件的所有区划，key是区划代码，value是区划名称。
    """
    src = codes_map.items()
    prefix = _code[:a]
    middle = '0' * (b - a)
    suffix = '0' * (12 - b)

    if not prefix:
        return {c: n for c, n in src if c[a:b] != middle and c.endswith(suffix)}

    if prefix and suffix:
        return {c: n for c, n in src if c.startswith(prefix) and c[a:b] != middle and c.endswith(suffix)}
    elif prefix:
        return {c: n for c, n in src if c.startswith(prefix) and c[a:b] != middle}
    else:
        return {}


@click.command('adc', short_help='查询某个或列出指定条件下的行政区划代码')
@click.option('-d', '--detail', 'detail', metavar='CODE', help='查询某个区划代码的详细信息。')
@click.option('-s', '--sub', 'parent', metavar='CODE', help='查询某个区划的所有直接子级区划。')
@click.option('-p', '--province', 'provinces', multiple=True, help='按省级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-c', '--city', 'cities', multiple=True, help='按市级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-k', '--county', 'counties', multiple=True, help='按县级代码(两位数字)筛选区划代码。可填多个。')
@click.option('-t', '--township', 'townships', multiple=True, help='按乡级代码(三位数字)筛选区划代码。可填多个。')
@click.option('-o', '--town', 'towns', multiple=True, help='按镇级代码(三位数字)筛选区划代码。可填多个。')
@click.option('-r', '--regex', type=Regex(), help='使用正则表达式筛选划代码。')
@click.option('-T', '--title', help='按名称筛选区划。')
@click.option('--purify', is_flag=True, help='不输出区划代码对应的名称。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def get_adcode(
        detail: str, parent: str,
        provinces, cities, counties, townships, towns,
        regex, title, purify,
):
    """查询某个或列出指定条件下的行政区划代码（Area Division Code）。"""
    ad_codes = lazy_load()
    if detail:
        code = detail.ljust(12, '0')[:12]
        print(code_detail.format(
            province=ad_codes.get(f'{code[:2]:012s}', '?'),
            city=ad_codes.get(f'{code[:4]:012s}', '?'),
            county=ad_codes.get(f'{code[:6]:012s}', '?'),
            township=ad_codes.get(f'{code[:9]:012s}', '?'),
            town=ad_codes.get(code, '?'),
            p=code[:2], c=code[2:4], k=code[4:6], t=code[6:9], o=code[9:],
        ))
        return
    if parent:
        parent = f'{parent[:12]:012s}'
        if parent == '000000000000':
            codes = search_code(0, 2, parent, ad_codes)
        elif parent.endswith('0000000000'):
            codes = search_code(2, 4, parent, ad_codes)
        elif parent.endswith('00000000'):
            codes = search_code(4, 6, parent, ad_codes)
            if len(codes) == 0:
                codes = search_code(6, 9, parent, ad_codes)
        elif parent.endswith('000000'):
            codes = search_code(6, 9, parent, ad_codes)
        elif parent.endswith('000'):
            codes = search_code(9, 12, parent, ad_codes)
        else:
            codes = {}
        codes = codes.items()
    else:
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
