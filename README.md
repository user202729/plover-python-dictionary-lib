# plover-python-dictionary-lib
Library for writing Python dictionary for Plover,
and generating JSON dictionary file from Python dictionary.

### Installation

This package is available on 
[PyPI](https://pypi.org/project/plover-python-dictionary-lib/).
To install it, run the command

```bash
pip install plover-python-dictionary-lib
```

This is required to use/run the Python dictionaries that use this library.

### Example & usage

* The most common use case would be a Cartesian product of various dictionaries.
* You can read
	* [`00_two_letter_fingerspelling_example` example dictionary file](https://github.com/user202729/plover-python-dictionary-lib/blob/main/example/00_two_letter_fingerspelling_example.py) (GitHub link) for an example (this one is the most well-documented example file, with common patterns and explanation),
	* the rest of the files in the [`example/` folder](https://github.com/user202729/plover-python-dictionary-lib/tree/main/example),
	* and the documentation (as Python docstrings) in the source code,
* Useful resources: [Frequently used dictionary components](https://github.com/user202729/plover-python-dictionary-lib/wiki/Frequently-used-dictionary-components) *(feel free to edit the wiki)*

### Generate JSON

The Python dictionary must be written with this plugin.

Call `.print_items()` on the main `Dictionary` object. (see also the example dictionaries above)

**Note**: because of [an incompatibility between Plover and the `plover_stroke` library](https://github.com/benoit-pierre/plover_stroke/issues/1),
sometimes the JSON dictionary may not work in Plover.

For example: if this code
is included at the end of the Python dictionary file named `dictionary.py`

```python
if __name__=="__main__":
	dictionary.print_items()
```

(assuming that the main dictionary object is named `dictionary`) then running `python dictionary.py`
will print the dictionary as JSON to the standard output.
