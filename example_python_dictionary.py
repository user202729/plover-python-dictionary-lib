#!/bin/python

# ======== Imports.
from plover.system import english_stenotype as e
# Alternatively
#    from plover import system as e
# can be used too, but then it will only work in Plover and only if the correct system is set.

from plover_python_dictionary_lib import get_context_from_system

# ======== Boilerplate to set up objects.
context=get_context_from_system(e)
s=context.SingleDictionary
stroke=context.stroke
translation=context.translation

# ======== Define constants.
leader_stroke="TP*EURPBG" # finger*
leader_stroke_2="TP*EURPBGS" # fingers*

# s(...): Creates a Dictionary object from a dict (or a list, for example, ["S"] is equivalent to {"S": "S"})
left_hand=s({
	'A':       'a',
	'PW':      'b',
	'KR':      'c',
	'TK':      'd',
	#'??':     'e',
	'TP':      'f',
	'TKPW':    'g',
	'H':       'h',
	#'??':     'i',
	'SKWR':    'j',
	'K':       'k',
	'HR':      'l',
	'PH':      'm',
	'TPH':     'n',
	'O':       'o',
	'P':       'p',
	'KW':      'q',
	'R':       'r',
	'S':       's',
	'T':       't',
	#'??':     'u',
	'SR':      'v',
	'W':       'w',
	'KP':      'x',
	'KWR':     'y',
	'STKPW':   'z',
	})

right_hand=s({
	#'??':     'a',
	'-B':      'b',
	#'??':     'c',
	'-D':      'd',
	'E':       'e',
	'-F':      'f',
	'-G':      'g',
	'*FD':     'h',
	'EU':      'i',
	'-PBLG':   'j',
	'-BG':     'k',
	'-L':     'l',
	'-PL':     'm',
	'-PB':     'n',
	#'??':     'o',
	'-P':      'p',
	#'??':     'q',
	'-R':      'r',
	'-S':      's',
	'-T':      't',
	'U':       'u',
	'-FB':     'v',
	#'??':     'w',
	'-BGS':    'x',
	'-FRL':    'y',
	'-Z':      'z',
	})

# ======== Main definitions.

# |: Compute the union of two dictionaries.
# *: Compute the (Cartesian) product of two dictionaries. The 2 adjacent strokes are merged.
one_stroke=left_hand | right_hand | left_hand*right_hand

# /: Compute the (Cartesian) product of two dictionaries. The 2 adjacent strokes are not merged.
dictionary = (
		s({leader_stroke: "{#}", leader_stroke_2: "{#}"}) |
		(stroke(leader_stroke) | stroke(leader_stroke_2)) / translation("{&") * one_stroke * translation("}") | 
		stroke(leader_stroke_2) / translation("{&") * one_stroke / one_stroke * translation("}")
		)

# ======== More boilerplate (the lambda is required because plover-python-dictionary only accept objects with function type as the lookup function

lookup=lambda strokes: dictionary.lookup_tuple(strokes)
LONGEST_KEY=dictionary.longest_key


# ======== demonstration part -- not necessary in a real Python dictionary
if __name__=="__main__":
	assert dictionary.longest_key==3

	for d in [dictionary,
			# map a part
			stroke(leader_stroke)/((left_hand*right_hand).map(lambda x: "{&" + x + "}")),

			# name a part for mapping (and to disable automatically concatenation behavior)
			stroke(leader_stroke)/((left_hand.named("left")*right_hand.named("right")).map(lambda left, right: "{&" + left + right + "}")),

			# map with keyword arguments
			stroke(leader_stroke)/((left_hand.named("left")*right_hand.named("right")).map(lambda **kwargs: "{&" + kwargs["left"] + kwargs["right"] + "}")),

			# not all parts must be named (those which don't are not accessible
			(stroke(leader_stroke)/(left_hand.named("left")*right_hand.named("right"))).map(lambda left, right: "{&" + left + right + "}"),
			(stroke(leader_stroke)/left_hand.named("left")*right_hand.named("right")).map(lambda left, right: "{&" + left + right + "}"),

			# name weird parts
			(stroke(leader_stroke).named("leader")/left_hand.named("left")*right_hand.named("right")).map(lambda leader, left, right: "{&" + left + right + "}"),
			]:
		for target, outline in [
		("{&ji}", "TP*EURPBG/SKWREU"),
		("{&jl}", "TP*EURPBG/SKWR-L"),
		(None   , "TP*EURPBG/SKWR-BL"),
		(None   , "SKWR-L"),
		]:
			result=d.lookup_str(outline)
			assert result==target, (outline, result, target)

	#dictionary.print_items()

	assert "a" == s({"A": "a"}).lookup_str("A")
	assert "a" == (s({"A": "a"}) | s({"-B": "b"})).lookup_str("A")
	assert "b" == (s({"A": "a"}) | s({"-B": "b"})).lookup_str("-B")
