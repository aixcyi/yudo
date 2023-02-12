from typing import TypeAlias

# https://rich.readthedocs.io/en/latest/appendix/colors.html
RichColorName: TypeAlias = str
# https://click.palletsprojects.com/en/8.1.x/api/#click.style
ClickColorName: TypeAlias = str

# Main Table (Help)
MT_ROW_LIGHT = RichColorName('')
MT_ROW_DARK = RichColorName('grey50')
MT_ROW = [MT_ROW_DARK, MT_ROW_LIGHT]
MT_DEPRECATED = RichColorName('dark_goldenrod')

# Printable Text
PT_WARNING = ClickColorName('yellow')
PT_ERROR = ClickColorName('red')
PT_SPECIAL = ClickColorName('magenta')
PT_CONF_SECTION = ClickColorName('yellow')
PT_CONF_KEY = ClickColorName('cyan')
PT_CONF_EQU = ClickColorName('yellow')

# url
URL_SECURITY_PROTOCOL = RichColorName('green')
