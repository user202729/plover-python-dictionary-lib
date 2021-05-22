# plover-python-dictionary-lib
Library for writing Python dictionary for Plover,
and generating JSON dictionary file from Python dictionary.

This package is available on 
[PyPI](https://pypi.org/project/plover-python-dictionary-lib/).
To install it, run the command

```bash
pip install plover-python-dictionary-lib
```


Example & usage: See [`example_python_dictionary.py`](https://github.com/user202729/plover-python-dictionary-lib/blob/main/example_python_dictionary.py) (on GitHub).

To generate JSON (the Python dictionary must be written with this plugin),
call `.print_items()` on the main `Dictionary` object. For example if this code
is included at the end of the Python dictionary file named `dictionary.py`

```python
if __name__=="__main__":
	dictionary.print_items()
```

(assuming that the main dictionary object is named `dictionary`) then running `python dictionary.py`
will print the dictionary as JSON to the standard output.
