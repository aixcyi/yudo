from clis.adcode import get_adcode
from clis.binary import generate_bits, generate_chars
from clis.configuration import configurate
from clis.datetime import enum_date, enum_datetime
from clis.frp import manage_frpc
from clis.idcard import enum_prcid
from clis.sequence import product_columns
from clis.util import split_url, encode_uri, decode_uri, get_length, run_command

interface_list = [
    get_adcode,
    generate_bits,
    generate_chars,
    enum_date,
    enum_datetime,
    enum_prcid,
    product_columns,
    split_url,
    encode_uri,
    decode_uri,
    get_length,
    configurate,
    manage_frpc,
    run_command,
]
