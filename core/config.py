import typing
from configparser import NoSectionError, DuplicateSectionError, NoOptionError
from os import PathLike
from pathlib import Path


class Section(dict):

    @property
    def is_proxy(self):
        return False

    def default(self, **defaults: typing.Any) -> typing.NoReturn:
        self.__ror__(defaults)


class SectionProxy(typing.MutableMapping):

    @property
    def is_proxy(self):
        return True

    def __init__(self, configurator: "Configurations", name: str):
        super().__init__()
        self._conf = configurator
        self._name = name

    def __repr__(self) -> str:
        return f'<Section(name="{self._name}")>'

    def __iter__(self) -> typing.KeysView[str]:
        return self._conf.get_options(self._name)

    def __len__(self) -> int:
        return len(self._conf.get_options(self._name))

    # ----------------

    def __contains__(self, key: str) -> bool:
        return self._conf.has_option(self._name, key)

    def __getitem__(self, option: str) -> str:
        return self._conf.get_option(self._name, option)

    def get(self, option: str, default=...) -> typing.Any:
        return self._conf.get_option(self._name, option)

    def __setitem__(self, key: str, value: typing.Any) -> typing.NoReturn:
        self._conf.set_option(self._name, key, value)

    def setdefault(self, option, value=None) -> typing.Any:
        return self._conf.setdefault_option(self._name, option, value)

    def __delitem__(self, key: str) -> typing.NoReturn:
        _ = self._conf.pop_option(self._name, key)

    def pop(self, key: str, default=...) -> typing.Any:
        return self._conf.pop_option(self._name, key, default=default)

    # ----------------

    def keys(self) -> typing.KeysView[str]:
        return self._conf.get_options(self._name)

    def values(self) -> typing.ValuesView[typing.Any]:
        return self._conf._sections[self._name].values()

    def items(self) -> typing.ItemsView[str, typing.Any]:
        return self._conf._sections[self._name].items()

    def __or__(self, values: dict[str, typing.Any]):
        self._conf.update_options(self._name, **values)
        return self

    def __ror__(self, values: dict[str, typing.Any]):
        self._conf.default_options(self._name, **values)
        return self

    def update(self, **values: typing.Any) -> typing.NoReturn:
        self._conf.update_options(self._name, **values)

    def default(self, **defaults: typing.Any) -> typing.NoReturn:
        self._conf.default_options(self._name, **defaults)

    def popitem(self) -> tuple[str, typing.Any]:
        return self._conf._sections[self._name].popitem()

    def clear(self) -> typing.NoReturn:
        self._conf.clear_options(self._name)


class Configurations(typing.MutableMapping):

    def __init__(self, *args, **kwargs):
        self._sections: dict[str, Section] = dict()
        self._proxies: dict[str, SectionProxy] = dict()

    def copy(self, *args, **kwargs) -> "Configurations":
        config = type(self)(*args, **kwargs)
        config._sections = dict((name, section.copy()) for name, section in self._sections.items())
        config._proxies = dict((name, SectionProxy(config, name)) for name in config._sections)
        return config

    def __repr__(self):
        cls = self.__class__.__name__
        sections = ', '.join(self._sections.keys())
        return f'<{cls}(sections=[{sections}])>'

    # ----------------

    def __contains__(self, title: str) -> bool:
        return title in self._sections

    def __getitem__(self, title: str) -> SectionProxy:
        if title not in self._sections:
            raise NoSectionError(title)
        return self._proxies[title]

    def get(self, title: str) -> SectionProxy:
        if title not in self._sections:
            raise NoSectionError(title)
        return self._proxies[title]

    def __setitem__(self, title: str, section: Section) -> typing.NoReturn:
        if section.__class__ is not Section:
            raise TypeError
        if title in self._sections:
            raise DuplicateSectionError(title)
        self._sections[title] = section
        self._proxies[title] = SectionProxy(self, title)

    def setdefault(self, title: str, default: Section = None) -> SectionProxy:
        if default is None:
            default = Section()
        elif default.__class__ is not Section:
            raise TypeError
        if title not in self._sections:
            self._sections[title] = default
            self._proxies[title] = SectionProxy(self, title)
        return self._proxies[title]

    def __delitem__(self, title: str) -> typing.NoReturn:
        if title not in self._sections:
            raise NoSectionError(title)
        del self._sections[title]
        del self._proxies[title]

    def pop(self, title: str, default=None) -> Section | None:
        if title not in self._sections:
            if default is None:
                return None
            elif default.__class__ is Section:
                return default
            else:
                raise NoSectionError(title)
        del self._proxies[title]
        return self._sections.pop(title)

    def popitem(self) -> tuple[str, Section]:
        if len(self._sections) == 0:
            raise NoSectionError('<Anything>')
        name, section = self._sections.popitem()
        del self._proxies[name]
        return name, section

    # ----------------

    def __len__(self) -> int:
        return len(self._sections)

    def __iter__(self) -> typing.KeysView[str]:
        return self._sections.keys()

    def keys(self) -> typing.KeysView[str]:
        return self._sections.keys()

    def values(self) -> typing.ValuesView[SectionProxy]:
        return self._proxies.values()

    def items(self) -> typing.ItemsView[str, SectionProxy]:
        return self._proxies.items()

    def __or__(self, sections: "Configurations"):
        if sections.__class__ is not Configurations:
            raise TypeError
        for title, section in sections._sections.items():
            # if section.__class__ is not Section:
            #     raise TypeError
            if title in self._sections:
                self._sections[title].update(section)
            else:
                self._sections[title] = section
                self._proxies[title] = SectionProxy(self, title)
        return self

    __ior__ = __or__

    def update(self, **kwargs: Section) -> typing.NoReturn:
        for title, section in kwargs.items():
            if section.__class__ is not Section:
                raise TypeError
            if title in self._sections:
                self._sections[title].update(section)
            else:
                self._sections[title] = section
                self._proxies[title] = SectionProxy(self, title)

    def default(self, **kwargs: Section) -> typing.NoReturn:
        for title, section in kwargs.items():
            if section.__class__ is not Section:
                raise TypeError
            if title in self._sections:
                self._sections[title].__ror__(section)
            else:
                self._sections[title] = section
                self._proxies[title] = SectionProxy(self, title)

    def reorder(self, ordering: list[str]) -> typing.NoReturn:
        requires = tuple(sorted(ordering))
        exists = tuple(sorted(self._sections.keys()))
        if requires != exists:
            raise ValueError
        self._sections = {title: self._sections[title] for title in ordering}

    def clear(self) -> typing.NoReturn:
        self._sections.clear()
        self._proxies.clear()

    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    def has_option(self, section: str, option: str, err=True) -> bool:
        if section in self._sections:
            return option in self._sections[section]
        if err:
            raise NoSectionError(section)
        else:
            return False

    def get_option(self, section: str, option: str, default=...) -> typing.Any:
        if section not in self._sections:
            raise NoSectionError(section)
        if option in self._sections[section]:
            return self._sections[section][option]
        if default is ...:
            raise NoOptionError(option, section)
        return default

    def set_option(self, section: str, option: str, value: typing.Any) -> typing.NoReturn:
        if section not in self._sections:
            raise NoSectionError(section)
        if option not in self._sections[section]:
            raise NoOptionError(option, section)
        self._sections[section][option] = value

    def setdefault_option(self, section: str, option: str, default=None) -> typing.Any:
        if section not in self._sections:
            raise NoSectionError(section)
        return self._sections[section].setdefault(option, default)

    def pop_option(self, section: str, option: str, default=...) -> typing.Any:
        if section not in self._sections:
            raise NoSectionError(section)
        if option in self._sections[section]:
            return self._sections[section][option]
        if default is ...:
            raise NoOptionError(option, section)
        return default

    # ----------------

    def get_options(self, section: str) -> typing.KeysView[str]:
        if section not in self._sections:
            raise NoSectionError(section)
        return self._sections[section].keys()

    def update_options(self, section: str, **values: typing.Any) -> typing.NoReturn:
        if section not in self._sections:
            raise NoSectionError(section)
        self._sections[section].update(**values)

    def default_options(self, section: str, **defaults: typing.Any) -> typing.NoReturn:
        if section not in self._sections:
            raise NoSectionError(section)
        self._sections[section].__ror__(defaults)

    def clear_options(self, section: str) -> typing.NoReturn:
        if section not in self._sections:
            raise NoSectionError(section)
        self._sections[section].clear()


class Configurator(Configurations):

    @classmethod
    def _init_path(cls, fp, auto_create=False) -> Path:
        path = fp.__fspath__() if isinstance(fp, PathLike) else fp
        path = Path(path)
        if not path.exists() and not auto_create:
            raise FileNotFoundError
        path.touch()
        return path

    def __init__(
            self,
            fp: str | PathLike,
            encoding='UTF-8',
            auto_save=False,
            ensure_file=False,
    ):
        super().__init__()
        self._code = encoding
        self._save = auto_save
        self._path = self._init_path(fp, ensure_file)

    def copy(self, fp: str | PathLike, **kwargs) -> "Configurator":
        config = Configurations.__new__(self.__class__)
        config.__init__(fp, **kwargs)
        config._sections = dict(
            (name, section.copy()) for name, section in self._sections.items()
        )
        config._proxies = dict(
            (name, SectionProxy(config, name)) for name in config._sections
        )
        return config

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._save:
            self.save()

    # ----------------

    def open(self) -> typing.NoReturn:
        with open(self._path, 'r', encoding=self._code) as f:
            self.load(f)

    def load(self, f: typing.TextIO | PathLike | str) -> typing.NoReturn:
        raise NotImplementedError

    def loads(self, text: str) -> typing.NoReturn:
        raise NotImplementedError

    # ----------------

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        file = self._path.name
        sections = ','.join(self._sections.keys())
        return f'<{cls}(file="{file}", sections=[{sections}])>'

    def save(self) -> typing.NoReturn:
        with open(self._path, 'w', encoding=self._code) as f:
            self.dump(f)

    def dump(self, f: typing.TextIO | PathLike | str) -> typing.NoReturn:
        raise NotImplementedError

    def dumps(self) -> str:
        raise NotImplementedError
