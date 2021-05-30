from typing import Dict, TypeVar, Union, NamedTuple, Optional, Any, Callable, List, Iterable, Tuple, Mapping
import functools
import sys
import operator
import itertools
import inspect
from types import SimpleNamespace
from plover_stroke import BaseStroke

#from functools import lru_cache
# note (if used) weakref? id? ==?

#from plover.system import english_stenotype as system

Context=SimpleNamespace

def concatenate_merge_function(*args, **kwargs)->str:
	return "".join(*args, *kwargs)

class StrokeSeparator: pass
stroke_separator=StrokeSeparator()

LookupResult=Optional[str]

#StrokeT=TypeVar("StrokeT")

InputStrokeType=Union[str, BaseStroke]
#InputStrokeType=Union[str, StrokeT]

InputStrokesType=Union[InputStrokeType, Iterable[InputStrokeType], Iterable[str]]

Strokes=Tuple[BaseStroke, ...]

def subsets(stroke_type: type, stroke: BaseStroke)->Iterable[BaseStroke]:
	for keys in itertools.product([[], [key]] for key in stroke.keys()):
		yield stroke_type(itertools.chain(keys))

def outline_union(a: Strokes, b: Strokes)->Strokes:
	return tuple(map(operator.or_, a, b))

def outline_union_strip_optional(a: Optional[Strokes], b: Optional[Strokes])->Strokes:
	assert a
	assert b
	return outline_union(a, b)

class Dictionary:
	def __init__(self, stroke_type: type)->None:
		self.stroke_type=stroke_type

	def lookup(self, strokes: Strokes)->Any:
		"""
		Lookup a stroke in the dictionary.
		Must not raise a KeyError.
		Return None if there's nothing found.

		Arguments:
			strokes: a RTF/CRE stroke string.
		"""
		raise NotImplementedError

	def lookup_str(self, strokes: str)->LookupResult:
		result=self.lookup(tuple(map(self.stroke_type, strokes.split("/"))))
		assert result is None or isinstance(result, str)
		return result

	def lookup_tuple(self, strokes: Tuple[str])->LookupResult:
		result=self.lookup(tuple(map(self.stroke_type, strokes)))
		assert result is None or isinstance(result, str)
		return result
	
	def items(self)->Iterable[Tuple[Strokes, Any]]:
		"""
		Return all items in the dictionary.
		"""
		raise NotImplementedError

	def items_str(self)->Iterable[Tuple[str, str]]:
		for key, value in self.items():
			assert isinstance(value, str)
			yield "/".join(str(stroke) for stroke in key), value

	def items_str_dict(self)->Dict[str, str]:
		"""
		Get the dictionary as a dict from str (RTF/CRE) to str.
		"""
		result_items=list(self.items_str())
		result=dict(result_items)
		assert len(result_items)==len(result)
		return result

	def print_items(self)->None:
		"""
		Print all items in the dictionary in JSON format.
		"""
		import json
		json.dump(self.items_str_dict(), sys.stdout, ensure_ascii=False, indent=0)

	def __or__(self, other: "Dictionary")->"Dictionary":
		"""
		Compute the union of two dictionaries.
		"""
		return AlternativeDictionary(self.stroke_type, [self, other])

	def __mul__(self, other: "Dictionary")->"Dictionary":
		"""
		Compute the (Cartesian) product of two dictionaries. The 2 adjacent strokes are merged.
		"""
		return ProductDictionary(self.stroke_type, self, other, merge=True)

	def __truediv__(self, other: "Dictionary")->"Dictionary":
		"""
		Compute the (Cartesian) product of two dictionaries. The 2 adjacent strokes are not merged.
		"""
		return ProductDictionary(self.stroke_type, self, other, merge=False)

	def map(self, function: Callable[..., Any])->"Dictionary":
		"""
		Map a function over the dictionary values.
		"""
		return MappedDictionary(self.stroke_type, self, function)

	def filter(self, condition: Callable[[Strokes, Any], Any])->"Dictionary":
		return FilteredDictionary(self.stroke_type, self, condition)

	def named(self, name: str)->"NamedDictionary":
		return NamedDictionary(self.stroke_type, self, name)

	outline_length: Optional[int]
	"""
	The length of the outlines in the dictionary, or None if the information is unknown.
	"""

	longest_key: int
	"""
	The longest_key in the dictionary.
	"""

	outline_mask: Optional[Strokes]
	"""
	The union mask of the outlines in the dictionary, or None if the information is unknown.
	"""


def to_stroke(stroke_type: type, stroke: InputStrokeType)->BaseStroke:
	# with the assertion
	assert isinstance(stroke, str) or isinstance(stroke, stroke_type)
	return stroke_type(stroke)


def to_strokes(stroke_type: type, strokes: InputStrokesType)->Strokes:
	if isinstance(strokes, str):
		return (stroke_type(strokes),)
	elif isinstance(strokes, BaseStroke):
		return (strokes,)
	elif isinstance(strokes, Iterable): # must handle str case before this one
		return tuple(to_stroke(stroke_type, stroke) for stroke in strokes)
	else:
		assert False


class CompoundResult(NamedTuple):
	"""
	Represent the lookup result of a product of dictionaries, or similar.
	"""
	data: Dict[str, Any]


class RawMappedDictionary(Dictionary):
	"""
	Represent a dictionary with a function mapped over the raw output of a given dictionary.
	If the given function returns None then there's no output.
	"""

	def __init__(self, stroke_type: type, wrapped: Dictionary, function: Callable[[Strokes, Any], Any])->None:
		super().__init__(stroke_type)
		self.wrapped=wrapped
		self.longest_key=wrapped.longest_key
		self.outline_length=wrapped.outline_length
		self.outline_mask=wrapped.outline_mask
		self.raw_mapped_function=function

	def lookup(self, strokes: Strokes)->Any:
		result=self.wrapped.lookup(strokes)
		if result is None: return None
		return self.raw_mapped_function(strokes, result)

	def items(self)->Iterable[Tuple[Strokes, Any]]:
		for strokes, value in self.wrapped.items():
			assert value is not None
			transformed_value=self.raw_mapped_function(strokes, value)
			if transformed_value is not None:
				yield strokes, transformed_value


class NamedDictionary(RawMappedDictionary):
	"""
	Represent a dictionary with an assigned name, for mapping.
	"""
	# note that keys after used once in map cannot be used in upper map layers.
	# unlike e.g. nested regex group
	# therefore it doesn't make sense to name a dictionary twice in a row

	def __init__(self, stroke_type: type, wrapped: Dictionary, name: str)->None:
		assert not isinstance(wrapped, NamedDictionary)
		self.name: str=name
		super().__init__(stroke_type, wrapped, self.name_result)

	def name_result(self, _strokes: Strokes, result: Any)->CompoundResult:
		assert not isinstance(result, CompoundResult), f"Cannot name already-named result -- old names: {list(result.data.keys())}, new name: {self.name}"
		return CompoundResult({self.name: result})


def apply_function(function: Callable, strokes: Strokes, result: Any)->Any:
	"""
	Apply a function on a resulting translation.

	Possible function signatures:

	f(result): Takes the raw result as input.
		Only applicable if result is not a CompoundResult.
		Does not support positional-only arguments.
	f(result, strokes) / f(strokes, result): Takes the raw result and the strokes as input.
		Only applicable if result is not a CompoundResult.
		Does not support positional-only arguments.
		The arguments must be named "result" and "strokes".
	f(name1, name2, name3): Takes the groups with the provided names as input.
		All available group names must be provided.
	f(name1, name2, name3, strokes): Same as above, also take the strokes.
	f(**kwargs): Same as above. kwargs["strokes"] will be available.
	
	"""
	include_strokes: bool=False
	try:
		argspec=inspect.getfullargspec(function)
		include_strokes=argspec.varkw is not None or "strokes" in argspec.args
	except TypeError:  # for built-in functions like str
		pass

	assert result is not None
	if isinstance(result, CompoundResult):
		assert "strokes" not in result.data
		if include_strokes:
			return function(strokes=strokes, **result.data)
		else:
			return function(**result.data)

	else:
		if include_strokes:
			return function(strokes=strokes, result=result)
		else:
			return function(result)


class MappedDictionary(RawMappedDictionary):
	def __init__(self, stroke_type: type, wrapped: Dictionary, function: Callable[..., Any])->None:
		super().__init__(stroke_type, wrapped, functools.partial(apply_function, function))
		self.mapped_function=function


class FilteredDictionary(RawMappedDictionary):
	def __init__(self, stroke_type: type, wrapped: Dictionary, condition: Callable[..., Any])->None:
		super().__init__(stroke_type, wrapped,
				lambda strokes, result: result if apply_function(condition, strokes, result) else None
				)


class SingleDictionary(Dictionary):
	"""
	Represent a constant explicitly-specified dictionary.
	"""
	def __init__(self, stroke_type: type, data: Union[Iterable[InputStrokesType], Dict[InputStrokesType, Any]])->None:
		super().__init__(stroke_type)
		self.data: Dict[Strokes, Any]
		if isinstance(data, Mapping):
			self.data={to_strokes(stroke_type, key): value for key, value in data.items()}
		elif isinstance(data, Iterable):
			self.data={to_strokes(stroke_type, strokes): strokes for strokes in data}
		else:
			assert False

		assert self.data
		self.outline_length=len(next(iter(self.data.keys())))
		self.longest_key=max(len(strokes) for strokes in self.data.keys())
		if any(len(strokes)!=self.outline_length for strokes in self.data.keys()):
			self.outline_length=None
		else:
			self.outline_mask=functools.reduce(
					outline_union,
					self.data.keys()
					)

	def lookup(self, strokes: Strokes)->Any:
		return self.data.get(strokes)

	def items(self)->Iterable[Tuple[Strokes, Any]]:
		return self.data.items()


class ProductDictionary(Dictionary):
	def __init__(self, stroke_type: type, a: Dictionary, b: Dictionary, merge: bool)->None:
		super().__init__(stroke_type)
		self.a=a
		self.b=b
		self.merge=merge
		assert a.outline_length
		assert b.outline_length
		assert a.outline_mask
		assert b.outline_mask
		self.outline_length=a.outline_length+b.outline_length-merge
		self.longest_key=a.longest_key+b.longest_key-merge
		if merge:
			x=a.outline_mask[-1]
			y=b.outline_mask[0]
			assert not (x&y), f"Cannot merge -- overlapping mask: {x} & {y}"
			self.outline_mask=a.outline_mask[:-1]+(x|y,)+b.outline_mask[1:]
		else:
			self.outline_mask=a.outline_mask+b.outline_mask

	def lookup(self, strokes: Strokes)->Any:
		if len(strokes)!=self.outline_length: return None
		assert self.outline_mask
		if any(a not in b for a, b in zip(strokes, self.outline_mask)): return None
		a, b=self.a, self.b
		assert a.outline_mask
		assert b.outline_mask
		if self.merge:
			before=strokes[:len(a.outline_mask)-1]
			common=strokes[len(a.outline_mask)-1]
			after=strokes[len(a.outline_mask):]
			strokes_a=before+(common&a.outline_mask[-1],)
			strokes_b=(common&b.outline_mask[0],)+after
		else:
			strokes_a=strokes[:len(a.outline_mask)]
			strokes_b=strokes[len(a.outline_mask):]

		value_a=a.lookup(strokes_a)
		if value_a is None: return None
		value_b=b.lookup(strokes_b)
		if value_b is None: return None

		return self.merge_value(value_a, value_b)

	def merge_stroke(self, strokes_a: Strokes, strokes_b: Strokes)->Strokes:
		if self.merge:
			assert (strokes_a[-1]+strokes_b[0])==(strokes_a[-1]|strokes_b[0])
			return strokes_a[:-1]+(strokes_a[-1]+strokes_b[0],)+strokes_b[1:]
		else:
			return strokes_a+strokes_b

	def merge_value(self, value_a: Any, value_b: Any)->Union[str, CompoundResult]:
		if isinstance(value_a, CompoundResult) or isinstance(value_b, CompoundResult):
			result=CompoundResult({})
			if isinstance(value_a, CompoundResult): result.data.update(value_a.data)
			if isinstance(value_b, CompoundResult): result.data.update(value_b.data)
		else:
			try:
				return value_a+value_b
			except TypeError:
				raise TypeError(f"Unsupported result types -- Left result: {value_a!r}, right result: {value_b!r}")
		return result

	def items(self)->Iterable[Tuple[Strokes, Any]]:
		for strokes_a, value_a in self.a.items():
			for strokes_b, value_b in self.b.items():
				yield self.merge_stroke(strokes_a, strokes_b), self.merge_value(value_a, value_b)


class SubsetDictionary(Dictionary):
	"""
	A dictionary formed as all the subsets of a particular set of keys.
	The corresponding value is a plover_stroke.BaseStroke object.
	"""
	def __init__(self, stroke_type: type, keys: InputStrokeType)->None:
		super().__init__(stroke_type)
		self.outline_mask=(to_stroke(stroke_type, keys),)
		self.outline_length=1
		self.longest_key=1

	def items(self)->Iterable[Tuple[Strokes, Any]]:
		assert self.outline_mask is not None
		for stroke in subsets(self.stroke_type, self.outline_mask[0]):
			yield stroke, stroke

	def lookup(self, strokes: Strokes)->Any:
		assert self.outline_mask is not None
		if len(strokes)==1 and strokes[0] in self.outline_mask[0]:
			return strokes[0]


class AlternativeDictionary(Dictionary):
	"""
	A dictionary formed as an alternative of multiple dictionaries.
	"""
	def __init__(self, stroke_type: type, components: List[Dictionary])->None:
		super().__init__(stroke_type)
		self._components: List[Dictionary]=[]
		for component in components:
			if isinstance(component, AlternativeDictionary):
				self._components.extend(component._components)
			else:
				self._components.append(component)

		assert self._components

		self.longest_key=max(component.longest_key for component in self._components)

		if any(component.outline_length is None
				or component.outline_length!=self._components[0].outline_length
				for component in self._components):
			self.outline_length=None
			self.outline_mask=None
		else:
			self.outline_length=self._components[0].outline_length
			self.outline_mask=functools.reduce(
					outline_union_strip_optional,
					(component.outline_mask for component in self._components)
					)

	def items(self)->Iterable[Tuple[Strokes, Any]]:
		for component in self._components:
			yield from component.items()

	def lookup(self, strokes: Strokes)->Any:
		for component in self._components:
			result=component.lookup(strokes)
			if result is not None: return result


def stroke(stroke_type: type, strokes: str)->Dictionary:
	"""
	Return a dictionary that has <strokes> as the stroke and nothing as the translation.
	Useful as part of a dictionary.

	The current implementation is not very efficient.
	"""
	return SingleDictionary(stroke_type, {strokes: ""})

def translation(stroke_type: type, translation: str)->Dictionary:
	"""
	Return a dictionary that has <translation> as the translation and nothing as the stroke.
	Useful as part of a dictionary.

	The current implementation is not very efficient.
	"""
	return SingleDictionary(stroke_type, {"": translation})

def get_context(stroke_type: type)->Context:
	return Context(
			Stroke            =stroke_type,
			stroke_type       =stroke_type,
			SingleDictionary  =functools.partial(SingleDictionary,  stroke_type),
			s                 =functools.partial(SingleDictionary,  stroke_type),

			stroke            =functools.partial(stroke,            stroke_type),

			translation       =functools.partial(translation,       stroke_type),

			filtered          =functools.partial(FilteredDictionary,stroke_type),
			FilteredDictionary=functools.partial(FilteredDictionary,stroke_type),

			subsets           =functools.partial(SubsetDictionary,  stroke_type),
			subsetd           =functools.partial(SubsetDictionary,  stroke_type),
			SubsetDictionary  =functools.partial(SubsetDictionary,  stroke_type),
			)

def get_context_from_system(system: Any)->Context:
	class Stroke_(BaseStroke): pass
	Stroke_.setup(system.KEYS, system.IMPLICIT_HYPHEN_KEYS, system.NUMBER_KEY, system.NUMBERS)
	return get_context(Stroke_)
