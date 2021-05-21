#!/bin/python
from plover.system import english_stenotype as e
# Alternatively
#    from plover import system as e
# can be used too, but then it will only work in Plover and only if the correct system is set.

from plover_python_dictionary_lib import get_context_from_system

context=get_context_from_system(e)

def merge_function(first_stroke, left, right):
	return "{&" + left + right + "}"

dictionary=context.SingleDictionary(merge_function,
	first_stroke="TP*EURPBG", # finger*
	stroke_separator="/",
	left={
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
		},
	right={
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
		},
	)

lookup=dictionary.lookup


# demonstration part -- not necessary in a real Python dictionary
if __name__=="__main__":
	print(lookup("TP*EURPBG/SKWREU"))
	print(lookup("TP*EURPBG/SKWR-L"))
	
	# currently not implemented
	#dictionary.print_items()
