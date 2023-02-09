import re
from configparser import ConfigParser
from pathlib import Path
from typing import Pattern

from click import ParamType, secho, echo

cfp = Path(__file__).parent.parent / 'yudo.ini'


def fmt_datasize(size: int) -> str:
    if size < 1024:
        return f'{size:d} Bytes'
    elif size < 1024 ** 2:
        return f'{size / 1024:.2f} KB'
    elif size < 1024 ** 3:
        return f'{size / 1024 ** 2:.2f} MB'
    elif size < 1024 ** 4:
        return f'{size / 1024 ** 3:.2f} GB'
    else:
        return f'{size / 1024 ** 4:.2f} TB'


class Regex(ParamType):
    name = 'regex'

    def convert(self, value: str, param, ctx) -> Pattern:
        try:
            return re.compile(value)
        except re.error:
            self.fail('正则表达式有误。', param, ctx)


def ask(dateset, force: bool) -> bool:
    qty = len(dateset)
    dsz = fmt_datasize(len(dateset[0]) * qty if dateset else 0)
    tip = f'预估数据量 {qty:d} 条，文本 {dsz}，确定继续？(Y/[n]) '
    if qty == 0:
        secho('没有产生任何数据。', err=True, fg='yellow')
        return False
    if force is False:
        echo(tip, err=True, nl=False)
        if input()[:1] != 'Y':
            return False
    return True


class YuConfiguration(ConfigParser):

    def __enter__(self):
        self.read(cfp, encoding='UTF-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def save_now(self):
        with open(cfp, 'w', encoding='UTF-8') as f:
            self.write(f)
