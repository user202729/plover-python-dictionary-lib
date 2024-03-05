# plover-python-dictionary-lib

[![PyPI](https://img.shields.io/pypi/v/plover-python-dictionary-lib?style=flat)](https://pypi.python.org/pypi/plover-python-dictionary-lib/)

Library for writing Python dictionary for Plover,
and generating JSON dictionary file from Python dictionary.

A Python dictionary is a Plover dictionary that is written in Python.
Refer to [documentation of the `plover-python-dictionary` package](https://pypi.org/project/plover-python-dictionary/)
to see what is the advantage of a Python dictionary.

This library provides some convenient helper tools to write a dictionary.

### Installation

This package is available on 
[PyPI](https://pypi.org/project/plover-python-dictionary-lib/).
To install it, run the command

```bash
pip install plover-python-dictionary-lib
```

This is required to use/run the Python dictionaries that use this library.

### Example & Usage

#### Getting started

This is a minimal example of a Python dictionary. You can save it as `helloworld.py` and load it into Plover, provided
`plover-python-dictionary` package is installed.

```python
#!/bin/python3
from plover.system import english_stenotype as e
from plover_python_dictionary_lib import get_context_from_system
context=get_context_from_system(e)
s=context.SingleDictionary
stroke=context.stroke
translation=context.translation

dictionary=s({
	"S": "hello world"
	})

lookup = lambda strokes: dictionary.lookup_tuple(strokes)
LONGEST_KEY = dictionary.longest_key

if __name__=="__main__":
	dictionary.print_items()
```

When loaded into Plover, it will define a dictionary with a single translation, as suggested by the `dictionary` variable.

It can also be run as a standalone Python script to print out the JSON dictionary it would corresponds to.
Refer to ["Generate JSON" section](#generate-json) for details.

#### Dictionary Operations

The power of the package comes from the variety of built-in functions that allows manipulating the components easily
to build up a whole dictionary.

When you have built up the desired dictionary, simply assign it to the `dictionary` variable, and set `lookup` and `LONGEST_KEY` correspondingly.

You can experiment with the operators simply by running the necessary imports in a Python shell;
alternatively, just run the Python file standalone to print out the content of the dictionary.

* The `|` operator
	* Compute the union of two dictionaries together (basically updating one dictionary with another as like a normal python dictionary)
```python
you = s({"KPWR": "you"})
they = s({"TWH": "they"})
dict1 = you | they
dict1.print_items()
# {"KPWR": "you", "TWH": "they"}
```

* The `*` operator
	* Compute the Cartesian product of two dictionaries such that:
		* Adjacent strokes are merged as according to steno order
		* Adjacent translations are merged using the `+` operator
	* Example:
```python
dict1 = s({
		"KPWR": "you",
		"TWH": "they"
	})
dict2 = s({
		"-R": " are"
	})
dict = dict1 * dict2
dict.print_items()
# {"KPWR-R": "you are", "TWH-R": "they are"}
```

#### `map()` method

Allows you to modify the content of an existing dictionary.
```python
>>> dict1 = s({"S": "is", "K": "can"})
>>> dict1.map(lambda x: x*2)
MappedDictionary({(S,): 'isis', (K,): 'cancan'})
```

You can also map over the keys provided the arguments are specially named as `strokes` and `result`:
```python
>>> dict1.map(lambda strokes, result: f"{result} ({strokes})")
MappedDictionary({(S,): 'is ((S,))', (K,): 'can ((K,))'})
```

You can also customize the argument names:

```python
def applyMods(mods, characters):
	for mod in mods:
		characters = f"{mod}({characters})"
	return characters
mods = s({"-R": ["shift"], "": []}).named("mods") 
characters = s({"A": "a"}).named("characters")
dict = (mods * characters).map(applyMods)
dict.print_items()
# {"AR": "shift(a)", "A": "a"}
```
In this case, `named("characters")` marks that the translation of the `characters` dictionary is
to be passed to the argument named `characters` in `applyMods`.

#### Extra

* You can read
	* [`00_two_letter_fingerspelling_example` example dictionary file](https://github.com/user202729/plover-python-dictionary-lib/blob/main/example/00_two_letter_fingerspelling_example.py) (GitHub link) for an example (this one is the most well-documented example file, with common patterns and explanation),
	* the rest of the files in the [`example/` folder](https://github.com/user202729/plover-python-dictionary-lib/tree/main/example),
	* and the documentation (as Python docstrings) in the source code,
* Useful resources: [Frequently used dictionary components](https://github.com/user202729/plover-python-dictionary-lib/wiki/Frequently-used-dictionary-components) *(feel free to edit the wiki)*

### Generate JSON

The Python dictionary must be written with this plugin.

Call `.print_items()` on the main `Dictionary` object. (see also the example dictionaries above)


For example: if this code
is included at the end of the Python dictionary file named `dictionary.py`

```python
if __name__=="__main__":
	dictionary.print_items()
```

(assuming that the main dictionary object is named `dictionary`) then running `python dictionary.py`
will print the dictionary as JSON to the standard output.

**Note**: If you get the error:
```
ModuleNotFoundError: No module named 'plover'
```
it means Plover was installed in a different Python *environment* from the environment that you ran the script in.

It depends on the operating-system and specific installation method how to run it in the correct environment. See https://github.com/user202729/plover-python-dictionary-lib/issues/4 for an example.

**Note** (fixed bug, affects old version only): because of [an incompatibility between Plover and the `plover_stroke` library](https://github.com/benoit-pierre/plover_stroke/issues/1),
sometimes the JSON dictionary may not work in Plover.
