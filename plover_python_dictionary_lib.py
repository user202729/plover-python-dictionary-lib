from typing import Dict, TypeVar, Union, NamedTuple, Optional, Any, Callable, List, Iterable, Tuple, Mapping
import functools
import sys
import operator
import itertools
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

	def print_items(self)->None:
		"""
		Print all items in the dictionary in JSON format.
		"""
		import json
		json.dump(dict(self.items_str()), sys.stdout, ensure_ascii=False, indent=0)

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
		import inspect
		argspec=inspect.getfullargspec(function)
		assert not argspec.varargs

		return MappedDictionary(self.stroke_type, self, function)

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


class NamedDictionary(Dictionary):
	"""
	Represent a dictionary with an assigned name, for mapping.
	"""
	# note that keys after used once in map cannot be used in upper map layers.

	def __init__(self, stroke_type: type, wrapped: Dictionary, name: str)->None:
		super().__init__(stroke_type)
		assert not isinstance(wrapped, NamedDictionary)
		self.wrapped=wrapped
		self.name=name
		self.longest_key=wrapped.longest_key
		self.outline_length=wrapped.outline_length
		self.outline_mask=wrapped.outline_mask

	def name_result(self, result: Any)->CompoundResult:
		assert not isinstance(result, CompoundResult)
		return CompoundResult({self.name: result})

	def lookup(self, strokes: Strokes)->Any:
		result=self.wrapped.lookup(strokes)
		if result is None: return None
		return self.name_result(result)

	def items(self)->Iterable[Tuple[Strokes, Any]]:
		for strokes, value in self.wrapped.items():
			yield strokes, self.name_result(value)



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
			assert not (x&y)
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
		if isinstance(value_a, str) and isinstance(value_b, str):
			return value_a+value_b
		result=CompoundResult({})
		if isinstance(value_a, CompoundResult): result.data.update(value_a.data)
		if isinstance(value_b, CompoundResult): result.data.update(value_b.data)
		return result

	def items(self)->Iterable[Tuple[Strokes, Any]]:
		for strokes_a, value_a in self.a.items():
			for strokes_b, value_b in self.b.items():
				yield self.merge_stroke(strokes_a, strokes_b), self.merge_value(value_a, value_b)



class MappedDictionary(Dictionary):
	def __init__(self, stroke_type: type, wrapped: Dictionary, function: Callable[..., Any])->None:
		super().__init__(stroke_type)
		self.function=function
		self.wrapped=wrapped
		self.longest_key=wrapped.longest_key
		self.outline_length=wrapped.outline_length
		self.outline_mask=wrapped.outline_mask

	def apply_function(self, strokes: Strokes, result: Any)->Any:

		#include_strokes=argspec.varkw is not None or "strokes" in argspec.args:
		#include_strokes_rtfcre=argspec.varkw is not None or "strokes_rtfcre" in argspec.args:
		#arguments={}
		#if include_strokes: arguments["strokes"]=strokes
		#if include_strokes_rtfcre: arguments["strokes_rtfcre"]=strokes_rtfcre

		if isinstance(result, CompoundResult):
			return self.function(**result.data)
		else:
			return self.function(result)

	def lookup(self, strokes: Strokes)->Any:
		result=self.wrapped.lookup(strokes)
		if result is None:
			return None
		return self.apply_function(strokes, result)

	def items(self)->Iterable[Tuple[Strokes, Any]]:
		for strokes, value in self.wrapped.items():
			yield strokes, self.apply_function(strokes, value)



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
			SingleDictionary=functools.partial(SingleDictionary, stroke_type),
			stroke=functools.partial(stroke, stroke_type),
			translation=functools.partial(translation, stroke_type),
			)

def get_context_from_system(system: Any)->Context:
	class Stroke_(BaseStroke): pass
	Stroke_.setup(system.KEYS, system.IMPLICIT_HYPHEN_KEYS, system.NUMBER_KEY, system.NUMBERS)
	return get_context(Stroke_)
