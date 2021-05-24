#!/bin/python
# Single Stroke Commands v1
# Source: http://www.openstenoproject.org/stenodict/dictionaries/single_stroke_commands.html
# (see also v2 at http://familyhoodchurch.blogspot.com/2019/06/single-stroke-commands.html)

from typing import List

from plover.system import english_stenotype as e
from plover_python_dictionary_lib import get_context_from_system

context=get_context_from_system(e)
s=context.SingleDictionary

main=s({
	"SHR": "Return",
	"KPW": "BackSpace",
	"PWR": "Delete",
	"TWH": "Down",
	"KPR": "Up",
	"WR": "Right",
	"SK": "Left",
	"TPWH": "End",
	"KPWR": "Home",
	"WHR": "Page_Down",
	"PHR": "Page_Up",
	"SP": "Space",
	"TKP": "Escape",
	"TKW": "Tab",
	"1": "F1",
	"2": "F2",
	"3": "F3",
	"4": "F4",
	"5": "F5",
	"A": "a",
	"PW": "b",
	"KR": "c",
	"TK": "d",
	"-E": "e",
	"TP": "f",
	"TKPW": "g",
	"H": "h",
	"-EU": "i",
	"SKWR": "j",
	"K": "k",
	"HR": "l",
	"PH": "m",
	"TPH": "n",
	"O": "o",
	"P": "p",
	"KW": "q",
	"R": "r",
	"S": "s",
	"T": "t",
	"-U": "u",
	"SR": "v",
	"W": "w",
	"KP": "x",
	"KWR": "y",
	"STKPW": "z",
})

mods=(
		s({"*": ["Control_L"], "": []}) *
		s({"-B": ["Shift_L"], "": []}) *
		s({
			"-FRLG": [],
			"-FRLGTS": ["Alt_L"],
			"-TSDZ": ["Super_L"],
			"-PTSDZ": ["Alt_L", "Super_L"],
			})
		)

def apply_modifiers(main, mods):
	for mod in mods:
		main=mod+"("+main+")"
	return "{#"+main+"}"

dictionary=(main.named("main") * mods.named("mods")).map(apply_modifiers)

lookup=lambda strokes: dictionary.lookup_tuple(strokes)
LONGEST_KEY=dictionary.longest_key
assert LONGEST_KEY==1

if __name__=="__main__":
	dictionary.print_items()
