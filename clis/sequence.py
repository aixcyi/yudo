from io import TextIOWrapper
from itertools import product
from re import fullmatch
from typing import Pattern

import click

from core.click_chore import Regex, ask
from core.style import *

RIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)


def patch_prc_checksum(number: str | tuple[str]) -> str:
    if len(digits := ''.join(number)) < 17:
        raise ValueError('提供的号码长度不能低于17位。')
    return digits[:17] + '10X98765432'[sum(map(lambda d, r: int(d) * r, digits, RIGHTS)) % 11]


@click.command('product', no_args_is_help=True, short_help='求多列文本的笛卡尔积')
@click.argument('files', type=click.File(encoding='UTF-8'), required=True, nargs=-1)
@click.option('-m', '--repeat', 'repetition', type=int, default=1, help='重复次数（将所有列作为一个整体进行重复）。')
@click.option('-0', '--skip-empty', is_flag=True, help='跳过行数为0的列。如果不选此项，'
                                                       '那么任意一列行数为0都会导致没有输出。')
@click.option('--patch-prc-sum', is_flag=True, help='计算并追加每个身份证号码的校验值。号码长度不能低于17位。')
@click.option('-f', '--format', 'fmt', help=r'用格式渲染每一行结果。每列用“{列序号}”代表，序号从0开始。')
@click.option('-r', '--regex', type=Regex(), help='过滤不能完全匹配正则表达式的结果。')
@click.option('-F', '--force', is_flag=True, help='不提示，直接输出。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def product_columns(
        files: tuple[TextIOWrapper],
        repetition: int,
        skip_empty: bool,
        patch_prc_sum: bool,
        fmt: str,
        regex: Pattern,
        force: bool,
):
    """
    求多列文本的笛卡尔积，每一列都是按行分隔的文本。使用文件输入。
    """
    if len(files) < 1:
        click.secho('至少需要一列（一个文件）。', err=True, fg=PT_WARNING)
        return
    if repetition < 1:
        click.secho('重复次数不能小于1。', err=True, fg=PT_ERROR)
        return

    if skip_empty:
        data = product(*(f.readlines() for f in files))
    else:
        data = product(*filter(None, (f.readlines() for f in files)))
    if patch_prc_sum:
        data = map(patch_prc_checksum, data)
    if fmt:
        data = map(lambda s: fmt.format(*s), data)
    if regex:
        data = filter(lambda s: fullmatch(regex, ''.join(s)), data)

    if ask(force=force, dataset=data):
        print('\n'.join(data))
