
__baseTable = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('a'),ord('a')+26)]

def encode(value):
	num = int(value)
	mid = []
	base = len(__baseTable)
	while True:
		if num == 0: break
		num,rem = divmod(num, base)
		mid.append(__baseTable[rem])

	return ''.join([str(x) for x in mid[::-1]])

def decode(value):
	array = list(str(value).lower())
	array.reverse()
	result = 0L
	base = len(__baseTable)
	for i, x in enumerate(array):
		result += __baseTable.index(x) * (base ** i)

	return result

	

if __name__ == '__main__':
	from random import randrange
	for test in range(1,10):
		v = randrange(1,1000000000000000)
		enc = encode(v)
		print "Number:%i, Encode: %s, Decode: %i" % (v,enc, decode(enc))