from typing import Dict, TypeVar, Union, NamedTuple, Optional, Any, Callable, List, Iterable, Tuple
import functools
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

StrokeT=TypeVar("StrokeT")

InputStrokeType=Union[str, StrokeT]

def get_context(stroke_type: Callable[..., StrokeT])->Context:
	Stroke: type=stroke_type

	def subsets(stroke: StrokeT)->Iterable[StrokeT]:
		import itertools
		for keys in itertools.product([[], [key]] for key in stroke.keys()):
			yield Stroke(itertools.chain(keys))

	def to_stroke(stroke: InputStrokeType)->StrokeT:
		# with the assertion
		assert isinstance(stroke, str) or isinstance(stroke, Stroke)
		return Stroke(stroke)

	class PartialStrokeLookup(NamedTuple):
		lookup: Callable[[StrokeT], LookupResult]  # must not raise
		keys: StrokeT
		keys_iterator: Callable[[], Iterable[StrokeT]]

	def lookup_function_str(keys: InputStrokeType,
			function: Callable[[str], LookupResult])->PartialStrokeLookup:
		"""
		Wraps a function that takes a string and returns the lookup result.

		The resulting function might raise KeyError.
		"""
		def result_lookup(stroke: StrokeT)->LookupResult:
			return function(stroke.rtfcre)
		return PartialStrokeLookup(result_lookup, to_stroke(keys), lambda: subsets(keys))

	def lookup_function_stroke(keys: Union[StrokeT, str],
			function: Callable[[StrokeT], LookupResult])->PartialStrokeLookup:
		"""
		Wraps a function that takes a Stroke object and returns the lookup result.

		The resulting function might raise KeyError.
		"""
		return PartialStrokeLookup(function, to_stroke(keys), lambda: subsets(keys))

	def parse_lookup(arg: Any)->Union[PartialStrokeLookup, StrokeSeparator]:
		if isinstance(arg, PartialStrokeLookup):
			return arg
		if isinstance(arg, str) and arg=="/":
			return stroke_separator
		if isinstance(arg, str):
			arg={arg: arg}
		if isinstance(arg, list):
			arg={item: item for item in arg}
		if isinstance(arg, dict):
			assert arg
			arg={to_stroke(key): value for key, value in arg.items()}
			keys=functools.reduce(operator.or_, arg.keys())
			return PartialStrokeLookup(arg.get, keys, lambda: arg.keys())
		assert False, ("Unrecognized format", arg)

	class Dictionary:
		def lookup(self, strokes: str)->LookupResult: # will not raise KeyError
			"""
			Lookup a stroke in the dictionary.

			Arguments:
				strokes: a RTF/CRE stroke string.
			"""
			raise NotImplementedError
		
		def items(self)->Iterable[Tuple[str, str]]:
			"""
			Return all items in the dictionary.
			"""
			raise NotImplementedError

		def print_items(self)->None:
			"""
			Print all items in the dictionary in JSON format.
			"""
			import json
			json.dumps(
					dict(self.items())
					, ensure_ascii=False, indent=0)


	class LookupObjectReference(NamedTuple):
		location: Union[int, str]
		lookup_object: PartialStrokeLookup

		@property
		def is_keyword(self)->bool:
			return isinstance(self.location, str)

	class StrokeComponents(NamedTuple):
		keys: StrokeT  # store the union of all PartialStrokeLookup keys to simplify implementation
		components: List[LookupObjectReference]

	class SingleDictionary(Dictionary):
		"""
		"""

		def __init__(self, merge_function, *args, **kwargs)->None:
			self.merge_function=merge_function
			self.args_component=[parse_lookup(arg) for arg in args]
			self.kwargs_component={key: parse_lookup(value) for key, value in kwargs.items()}

			components_: List[List[LookupObjectReference]]=[
					list(group)
					for is_lookup, group in itertools.groupby(
						[
							LookupObjectReference(index, lookup_object_or_separator) # type: ignore
							for index, lookup_object_or_separator in enumerate(self.args_component)] +
						[
							LookupObjectReference(key, lookup_object_or_separator) # type: ignore
							for key, lookup_object_or_separator in self.kwargs_component.items()]
						, key=lambda x: isinstance(x.lookup_object, PartialStrokeLookup)
						)
					if is_lookup]

			self.components: List[StrokeComponents]=[]
			for stroke_components in components_:
				keys=Stroke()
				for lookup_object_reference in stroke_components:
					new_keys: StrokeT=lookup_object_reference.lookup_object.keys
					assert not (keys&new_keys)
					keys|=new_keys
				self.components.append(StrokeComponents(keys, stroke_components))

		def lookup(self, strokes: str)->LookupResult:
			strokes_1=strokes.split("/")
			if len(strokes_1)!=len(self.components):
				return None
			strokes_: List[StrokeT]=[Stroke(stroke) for stroke in strokes_1]
			for stroke, stroke_components in zip(strokes_, self.components):
				if stroke not in stroke_components.keys:
					return None

			merge_args: List[Any]=[]  # anything that the component functions results
			merge_kwargs: Dict[str, Any]={}
			for stroke, stroke_components in zip(strokes_, self.components):
				for lookup_object_reference in stroke_components.components:
					component: StrokeT=stroke&lookup_object_reference.lookup_object.keys
					result=lookup_object_reference.lookup_object.lookup(component)
					if lookup_object_reference.is_keyword:
						assert isinstance(lookup_object_reference.location, str)
						assert lookup_object_reference.location not in merge_kwargs
						merge_kwargs[lookup_object_reference.location]=result
					else:
						assert len(merge_args)==lookup_object_reference.location
						merge_args.append(result)

			try:
				return self.merge_function(*merge_args, **merge_kwargs)
			except KeyError:
				return None

		def __or__(self, other: Dictionary)->"MultipleDictionary":
			return MultipleDictionary(self)|other

		def __items__(self)->Iterable[Tuple[str, str]]:
			raise NotImplementedError

	class MultipleDictionary(Dictionary):
		def __init__(self, arg: Any)->None:
			self.dictionaries: List[SingleDictionary]=[]
			if isinstance(arg, SingleDictionary):
				self.dictionaries=[arg]
			elif isinstance(arg, MultipleDictionary):
				self.dictionaries=list(arg.dictionaries)
			else:
				assert isinstance(arg, list)
				for dictionary in arg:
					assert isinstance(dictionary, SingleDictionary)
				self.dictionaries=arg

		def lookup(self, strokes: str)->LookupResult:
			for dictionary in self.dictionaries:
				result=dictionary.lookup(strokes)
				if result is not None:
					return result
			return None

		def __or__(self, other: Dictionary)->"MultipleDictionary":
			if isinstance(other, SingleDictionary):
				other=MultipleDictionary(other)
			return MultipleDictionary(self.dictionaries+other.dictionaries)

		def __items__(self)->Iterable[Tuple[str, str]]:
			return itertools.chain.from_iterable(
					dictionary.items()
					for dictionary in self.dictionaries
					)


	return Context(
			lookup_function_str=lookup_function_str,
			lookup_function_stroke=lookup_function_stroke,
			Dictionary=Dictionary,
			SingleDictionary=SingleDictionary,
			)

def get_context_from_system(system: Any)->Context:
	class Stroke_(BaseStroke): pass
	Stroke_.setup(system.KEYS, system.IMPLICIT_HYPHEN_KEYS, system.NUMBER_KEY, system.NUMBERS)
	return get_context(Stroke_)
