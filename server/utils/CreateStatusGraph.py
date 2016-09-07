#
# CreateStatusGraph.py
# Reads a status file (pickle), calculates code 
# coverage and graphs the bitmap in PNG format
#

import sys
import pickle

try:
	import png
	HAS_PYPNG = True

except:
	print "[!] PyPNG library not found."
	print "[*] Install via PIP: pip install pypng"
	HAS_PYPNG = False


def populate_array(bitmap):
	""" Array of RGB values for the PNG file """
	width = 256
	height = 256
	p = []

	for i in xrange(height):
	    row = []
	    for j in xrange(width):
	    	idx = i * height + j
	    	n = bitmap[idx]

	    	if not n:
	    		rgb = (0, 0, 0)
	    	else:
	    		rgb = get_rgb_from_value(n)

	        row.append(rgb)
	    p.append(row)

	return p


def get_rgb_from_value(n):
	""" Bins and some bit shifting """
	if n < 2:
		k = 0xFF0000
	elif n < 4:
		k = 0xFFFF00
	elif n < 8:
		k = 0x009900
	elif n < 32:
		k = 0x0080FF
	elif n < 128:
		k = 0x00FFFF
	else:
		k = 0xFFFFFF

	R = (k & 0xFF0000) >> 16 
	G = (k & 0x00FF00) >> 8
	B = (k & 0x0000FF)

	return (R, G, B)


def get_coverage(bitmap):
	""" Consider only not null values """
	total = len(bitmap)
	covered = total - bitmap.count(0)
	coverage = ((covered + 0.0) / total) * 100

	return coverage


def main():
	if len(sys.argv) != 2:
		print "python %s <filename>" % sys.argv[0]
		sys.exit(1)

	try:
		filename = sys.argv[1]
		with open(filename, 'rb') as f:
			saved_state = pickle.load(f)
		
		bitmap = saved_state['bitmap']

	except:
		print "[!] Could not load bitmap"
		sys.exit(1)

	# Get rough code coverage value
	coverage = get_coverage(bitmap)
	print "[*] Code coverage (basic block calls): %.2f" % coverage

	if HAS_PYPNG:		
		# Create PNG image from bitmap values
		p = populate_array(bitmap)
		img = png.from_array(p, 'RGB')
		img.save('status_graph.png')

		print "[*] Created PNG file"


if __name__ == '__main__':
	main()
