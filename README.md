# Argos Translate GUI

[Website](https://www.argosopentech.com) | [GitHub](https://github.com/argosopentech/argos-translate-gui) | [PyPI](https://pypi.org/project/argostranslategui/)

Graphical user interface for [Argos Translate](https://github.com/argosopentech/argos-translate).

![Screenshot](/img/Screenshot.png)
![Screenshot2](/img/Screenshot2.png)

## Install
```
pip3 install argostranslategui


```

## Translations

The interface automatically follows the system locale when a compiled Qt
translation catalog is available. Translation sources live in `translations/`
as `.ts` files and are compiled to `.qm` files during `build_py`; compiled
catalogs are build artifacts and are not committed to source control. A
catalog is compiled only when more than 20% of its messages are translated.
