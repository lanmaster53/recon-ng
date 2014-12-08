#
# python code to play around with netblocks.
#
# NOTEZ BIEN: use of long integers is deliberate, because it insures that
# various comparisons work right (eg 'low < high', when low has the high
# bit clear and high has it set).
import string

import ranges

# mask off 32 bits.
B32M = 0xffffffffL

def m32(n):
	"""Mask a number to 32 bits."""
	return n & B32M

def lenmask(len):
	"""Return the mask for a given network length"""
	return m32(-(1L<<(32-len)))

def cidrrange((addr, len)):
	"""Given an IP address and a network size, return the low and high addresses in it."""
	m = lenmask(len)
	# the low end is addr & mask (to make sure no funny business is going
	# on)
	l = addr&m
	# the high end is the low end plus the maximum span of the mask:
	h = l + m32(~0 ^ m)
	return (l, h)

def strtoip(ipstr):
	"""convert an IP address in string form to numeric."""
	res = 0L
	count = 0
	n = string.split(ipstr, '.')
	for i in n:
		res = res << 8L
		ot = string.atoi(i)
		if ot < 0 or ot > 255:
			raise ValueError, "invalid IP octet"
		res = res + ot
		count = count + 1
	# could be incomplete (short); make it complete.
	while count < 4:
		res = res << 8L
		count = count + 1
	return res
def strtocidr(ips):
	"""returns CIDR start + length from string"""
	rng = 32
	pos = string.find(ips, '/')
	if not pos == -1:
		rng = string.atoi(ips[pos+1:])
		ips = ips[:pos]
	if string.find(ips, '.') == -1:
		ip = string.atol(ips)
	else:
		ip = strtoip(ips)
	if rng < 0 or rng > 32:
		raise ValueError, "CIDR length out of range"
	return (ip, rng)
def cidrtostr(ip, len):
	if len == 32:
		return iptostr(ip)
	else:
		return '%s/%d' % (iptostr(ip), len)

def octet(ip, n):
	"""get octet n (0-3) of ip address ip. 0 is the first (left) octet."""
	s = (3-n) * 8
	return (ip >> s) & 0xff

def iptostr(ip):
	"""Convert IP number to string form"""
	o1, o2, o3, o4 = octet(ip,0), octet(ip,1), octet(ip,2), octet(ip,3)
	return '%d.%d.%d.%d' % (o1, o2, o3, o4)


def ffs(n):
	"""find first set bit in a 32-bit number"""
	r = 0
	while r < 32:
		if (1<<r)&n:
			return r
		r = r+1
	return -1

def lhcidrs(lip, hip):
	"""Convert a range from lowip to highip to a set of address/mask values."""
	r = []
	while lip <= hip:
		# algorithm:
		# try successively smaller length blocks starting at lip
		# until we find one that fits within lip,hip. add it to
		# the list, set lip to one plus its end, keep going.
		# we must insure that the chosen mask has lip as its proper
		# lower end, and doesn't go lower.
		lb = ffs(lip)
		if lb == -1:
			lb = 32
		while lb >= 0:
			(lt, ht) = cidrrange((lip, (32-lb)))
			if lt == lip and ht <= hip:
				break
			lb = lb - 1
		if lb < 0:
			raise ArithmeticError, "something horribly wrong"
		r.append((lip, (32-lb)))
		lip = ht+1
	return r

# This class handles network blocks.
class IpAddrRanges(ranges.Ranges):
	"""Sets of IP address ranges.

	All IP address arguments are supplied as strings."""
	def __init__(self):
		ranges.Ranges.__init__(self)
	# debugging routine to dump raw contents in comprehensible form.
       	def _dump(self):
		return map(lambda x: (iptostr(x[0]), iptostr(x[1])), self._l)
	def addcidr(self, ipstr):
		"""Add CIDR IP address range to the set."""
		(low, high) = cidrrange(strtocidr(ipstr))
		self.add(low, high)
	def addipr(self, i1, i2):
		"""Add all IP addresses between LOW and HIGH to the set."""
		low, high = strtoip(i1), strtoip(i2)
		self.add(low, high)
	def remcidr(self, ipstr):
		"""Remove CIDR IP address range from the set."""
		(low, high) = cidrrange(strtocidr(ipstr))
		self.remove(low, high)
	def remipr(self, i1, i2):
		"""Remove all IP addresses between LOW and HIGH from the set."""
		low, high = strtoip(i1), strtoip(i2)
		self.remove(i1, i2)
	def dumpnbstrs(self):
		"""Dump the contents of the set as a list of CIDR IP netblocks"""
		l = []
		for i in self._l:
			l = l + lhcidrs(i[0], i[1])
		return map(lambda x: cidrtostr(x[0], x[1]), l)
	def addstr(self, str):
		"""Add a string representing an IP address or CIDR range to us."""
		pos = string.find(str, '-')
		if pos == -1:
			self.addcidr(str)
		else:
			self.addipr(str[:pos], str[pos+1:])

		
# Validate a string as a CIDR netblock or IP address.
import re
cvalid = re.compile('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(/\d{1,2})?$')
def cidrstrerr(str):
	"""Check an IP address or CIDR netblock for validity.

	Returns None if it is and otherwise an error string."""
	if not cvalid.match(str):
		return 'Not a syntatically valid IP address or netblock'
	rng = 32
	pos = string.find(str, '/')
	ips = str
	if not pos == -1:
		rng = string.atoi(ips[pos+1:])
		ips = str[:pos]
	if rng < 0 or rng > 32:
		return 'CIDR length out of range'
	n = string.split(ips, '.')
	for i in n:
		ip = string.atoi(i)
		if (ip < 0 or ip > 255):
			return 'an IP octet is out of range'
	# could check to see if it is 'proper', but.
	return None
def cidrproper(str):
	(ip, rng) = strtocidr(str)
	(l, h) = cidrrange((ip, rng))
	if l != ip:
		return None
	else:
		return 1
