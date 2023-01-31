import re
from typing import Pattern

from click import ParamType, secho, echo

from core.meaningfuls import fmt_datasize


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
