#
# Sets of ranges of (integer) numbers.

class Ranges:
	"""Represent a set of integer ranges.

	Ranges represent a set of ranges of numbers. A new range
	or a list of them may be added to or deleted from the set.
	Adjacent ranges are merged in the set to create the minimal
	set of ranges necessary to cover all included numbers.

	Range sets support addition and subtraction operations.
	Eg: Ranges(1,10) + Ranges(2,30) + Ranges(50,60) - Ranges(14,28)"""
	def __init__(self, start=None, end=None):
		"""Optional START,END arguments become the initial range."""
		self._l = []
		if start and end:
			self._l.append([start,end])
	def dump(self):
		"""Returns the current content of the ranges."""
		return self._l
	def _find(self, start):
		i = 0
		while i < len(self._l):
			if start <= self._l[i][0]:
				break
			i = i + 1
		return i
	def _isprev(self, i):
		return not (i == 0)
	def _prev(self,i):
		return self._l[i-1]
		
	def add(self, start, end):
		"""And a range from START to END to the set."""
		# we store ranges sorted by start. find where it should go.
		i = self._find(start)
		# too large to fit:
		if i == len(self._l):
			self._l.append([start, end])
		else:
			r = self._l[i]
			# does it fit entirely inside an existing one?
			if start >= r[0] and end <= r[1]:
				return
			# glue it in in order; right now, ordered by start.
			self._l.insert(i, [start, end])
		# now we fix up the list by merging adjacent or overlapping
		# entries. We start from where we inserted, or 1 if we
		# inserted at 0, so we always have a previous entry.
		# if the list is length 1, this loop will do nothing.
		i = max(i, 1)
		while i < len(self._l):
			# attempt to merge with previous entry
			ro = self._l[i-1]
			r = self._l[i]
			# if front is adjacent or inside their back, we
			# are either inside them, or we are merging.
			if r[0]-1 <= ro[1]:
				# we must use max(), because we may be inside
				# them.
				ro[1] = max(r[1], ro[1])
				del self._l[i]
			elif r[0] == start and r[1] == end:
				# if we are currently looking at ourselves,
				# we need to look one afterwards too, in case
				# we are merging *up*. (I am not entirely sure
				# that this logic is still correct. See del.)
				i = i + 1
			else:
				# if we have done no work now, we will never
				# do any more.
				break
	def remove(self, start, end):
		"""Remove the range START to END from the set."""
		i = self._find(start)
		# deal with the previous block.
		# the previous block axiomatically has something in it after
		# we're done, because it starts before the range.
		if self._isprev(i) and start <= self._prev(i)[1]:
			r = self._prev(i)
			oe = r[1]
			# this is always correct:
			r[1] = start-1
			# however, we may need to split it.
			if end < oe:
				self._l.insert(i, [end+1, oe])
		# we may need to delete forward:
		while i < len(self._l):
			r = self._l[i]
			if r[0] > end:
				break
			# the range may be entirely contained in what we're
			# removing, or it may be only partially included.
			if r[1] <= end:
				del self._l[i]
			else:
				r[0] = end+1
	def isin(self, val):
		"""Is VAL a point in the set of ranges?"""
		for r in self._l:
			if val >= r[0] and val <= r[1]:
				return 1
		return None

	# we could attempt to define arithmetic operations on ranges,
	# but I think it would come to a horrible end due to stuff, and
	# it would involve a lot of copying.
	def addl(self, l):
		"""Add a list of [start,end] ranges to the set."""
		for s,e in l:
			self.add(s, e)
	def removel(self, l):
		"""Remove a list of [start,end] ranges from the set."""
		for s,e in l:
			self.remove(s, e)
	# on the other hand, what's copying in python?
	def _clone(self):
		n = self.__class__()
		for s,e in self._l:
			n._l.append([s,e])
		return n
	def __add__(self, other):
		n = self._clone()
		for s,e in other._l:
			n.add(s,e)
		return n
	def __sub__(self, other):
		n = self._clone()
		for s,e in other._l:
			n.remove(s,e)
		return n

	def __eq__(self, other):
		if len(other._l) != len(self._l):
			return 0
		for i in xrange(0, len(self._l)):
			if self._l[i] != other._l[i]:
				return 0
		return 1
	# okay, just what *is* the length of a range?
	# in this case it is the number of distinct subranges it has.
	def __len__(self):
		return len(self._l)
	def __cmp__(self, other):
		if self.__eq__(other):
			return 0
		# invalid to use except as ==, so I don't CARE.
		return 1
