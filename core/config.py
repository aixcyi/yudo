import typing
from collections import OrderedDict
from configparser import NoSectionError, NoOptionError
from os import PathLike
from pathlib import Path


class Configuration(typing.MutableMapping):
    """
    一个用于管理具有 “文件-节-键-值” 层级结构数据的类。
    这种结构与ini文件或cfg文件类似。
    """

    # 对应 file - section - option - value

    def __init__(
            self,
            fp: str | PathLike,
            encoding='UTF-8',
            auto_save=False,
            ensure_file=True,
    ):
        self._sections: OrderedDict[str, Section] = OrderedDict()
        self._proxies: OrderedDict[str, SectionProxy] = OrderedDict()
        self._code = encoding
        self._save = auto_save
        self._path = fp if isinstance(fp, str) else fp.__fspath__()
        p = Path(self._path)
        if not p.exists() and ensure_file:
            p.touch()
        if not p.is_file():
            raise FileNotFoundError(self._path)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._save:
            self.save()

    # ================ (?) to configs ================

    def open(self) -> typing.NoReturn:
        with open(self._path, 'r', encoding=self._code) as f:
            self.load(f)

    def load(self, f: typing.TextIO | PathLike | str) -> typing.NoReturn:
        raise NotImplementedError

    def loads(self, text: str) -> typing.NoReturn:
        raise NotImplementedError

    # ================ configs to (?) ================

    def __repr__(self) -> str:
        sections = ','.join(self._sections.keys())
        return f'<Configuration(sections=[{sections}])>'

    def save(self) -> typing.NoReturn:
        with open(self._path, 'w', encoding=self._code) as f:
            self.dump(f)

    def dump(self, f: typing.TextIO | PathLike | str) -> typing.NoReturn:
        raise NotImplementedError

    def dumps(self) -> str:
        raise NotImplementedError

    # ================ section(s) ================

    def __len__(self) -> int:
        return len(self._sections)

    def __iter__(self) -> typing.KeysView[str]:
        return self._sections.keys()

    def keys(self) -> typing.KeysView[str]:
        return self._sections.keys()

    def sections(self) -> typing.KeysView[str]:
        return self._sections.keys()

    def clear(self) -> typing.NoReturn:
        self._sections.clear()
        self._proxies.clear()

    def popitem(self) -> tuple[str, "Section"]:
        for name in reversed(self.sections()):
            section = self._sections.pop(name)
            del self._proxies[name]
            return name, section
        raise KeyError

    def update(self, **kwargs: "Section") -> typing.NoReturn:
        assert all(v.__class__ is Section for v in kwargs.values())
        self._sections.update(**kwargs)

    def values(self):  # -> typing.ValuesView["SectionProxy"]:
        return self._proxies.values()

    def items(self) -> typing.ItemsView[str, "SectionProxy"]:
        return self._proxies.items()

    # ----------------

    def __contains__(self, section: str) -> bool:
        return section in self._sections

    def __getitem__(self, name: str) -> "SectionProxy":
        if name not in self._proxies:
            raise NoSectionError(name)
        return self._proxies[name]

    def get(self, name: str) -> "SectionProxy":
        if name not in self._proxies:
            raise NoSectionError(name)
        return self._proxies.get(name)

    def __setitem__(self, name: str, section: "Section") -> typing.NoReturn:
        assert section.__class__ is Section
        if name not in self._sections:
            self._proxies[name] = SectionProxy(self, name)
        self._sections[name] = section

    def __delitem__(self, name: str) -> typing.NoReturn:
        if name not in self._sections:
            raise NoSectionError(name)
        self._sections.__delitem__(name)
        self._proxies.__delitem__(name)

    def pop(self, name: str) -> "Section":
        if name not in self._sections:
            raise NoSectionError(name)
        _ = self._proxies.pop(name)
        return self._sections.pop(name)

    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    # 以下方法不应直接使用

    def options(self, section: str) -> typing.KeysView[str]:
        if section not in self._sections:
            raise NoSectionError(section)
        return self._sections[section].keys()

    def update_options(self, section: str, **values: "Section") -> typing.NoReturn:
        assert all(v.__class__ is Section for v in values.values())
        if section not in self._sections:
            raise NoSectionError(section)
        self._sections[section].update(**values)
        # self._sections[section] = self._sections[section] | values

    def update_defaults(self, section: str, **defaults: typing.Any) -> typing.NoReturn:
        if section not in self._sections:
            raise NoSectionError(section)
        self._sections[section].__ror__(defaults)

    def pop_option_item(self, section: str, last=True) -> tuple[str, typing.Any]:
        if section not in self._sections:
            raise NoSectionError(section)
        orders = self._sections[section].keys()
        orders = reversed(orders) if last else orders

        for option in orders:
            value = self._sections[section][option]
            return option, value
        raise KeyError

    def clear_options(self, section: str) -> typing.NoReturn:
        if section not in self._sections:
            raise NoSectionError(section)
        self._sections[section].clear()

    # ----------------

    def has_option(self, section: str, option: str) -> bool:
        if section not in self._sections:
            raise NoSectionError(section)
        return option in self._sections[section]

    def pop_option(self, section: str, option: str, default=...) -> typing.Any:
        if section not in self._sections:
            raise NoSectionError(section)
        if option not in self._sections[section]:
            if default is ...:
                raise NoOptionError(option, section)
            return default
        return self._sections[section].pop(option)

    def get_option(self, section: str, option: str, default=...) -> typing.Any:
        if section not in self._sections:
            raise NoSectionError(section)
        if option not in self._sections[section]:
            if default is ...:
                raise NoOptionError(option, section)
            return default
        return self._sections[section][option]

    def set_option(self, section: str, option: str, value: typing.Any) -> typing.NoReturn:
        if section not in self._sections:
            raise NoSectionError(section)
        if option not in self._sections[section]:
            raise NoOptionError(option, section)
        self._sections[section][option] = value

    def set_default(self, section: str, option: str, default=None) -> typing.Any:
        if section not in self._sections:
            raise NoSectionError(section)
        return self._sections[section].setdefault(option, default)


class Section(OrderedDict):

    def update_defaults(self, **defaults: typing.Any) -> typing.NoReturn:
        self.__ror__(defaults)


class SectionProxy(typing.MutableMapping):

    def __init__(
            self,
            configurator: Configuration,
            name: str,
    ):
        super().__init__()
        self._conf = configurator
        self._name = name

    def __repr__(self) -> str:
        return f'<Section(name="{self._name}")>'

    def __iter__(self) -> typing.KeysView[str]:
        return self._conf.options(self._name)

    def __len__(self) -> int:
        return len(tuple(self._conf.options(self._name)))

    def __contains__(self, key: str) -> bool:
        return self._conf.has_option(self._name, key)

    def __getitem__(self, option: str) -> str:
        return self._conf.get_option(self._name, option)

    def get(self, option: str, default=...) -> typing.Any:
        return self._conf.get_option(self._name, option)

    def __setitem__(self, key: str, value: typing.Any) -> typing.NoReturn:
        self._conf.set_option(self._name, key, value)

    def setdefault(self, option, value=None) -> typing.Any:
        return self._conf.set_default(self._name, option, value)

    def __delitem__(self, key: str) -> typing.NoReturn:
        _ = self._conf.pop_option(self._name, key)

    def keys(self) -> typing.KeysView[str]:
        return self._conf.options(self._name)

    def values(self) -> typing.ValuesView[typing.Any]:
        return self._conf._sections[self._name].values()

    def items(self) -> typing.ItemsView[str, typing.Any]:
        return self._conf._sections[self._name].items()

    def pop(self, key: str, default=...) -> typing.Any:
        return self._conf.pop_option(self._name, key, default=default)

    def popitem(self, last=True) -> tuple[str, typing.Any]:
        return self._conf.pop_option_item(self._name, last=last)

    def __or__(self, values: Section):
        self._conf.update_options(self._name, **values)

    def update(self, **values: typing.Any) -> typing.NoReturn:
        self._conf.update_options(self._name, **values)

    def update_defaults(self, **defaults: typing.Any) -> typing.NoReturn:
        self._conf.update_defaults(self._name, **defaults)

    def clear(self) -> typing.NoReturn:
        self._conf.clear_options(self._name)
