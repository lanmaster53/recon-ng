'''Regression tests for Framework.table() column width expansion.

When a title is wider than the rendered data columns, the framework shares
the surplus width across the columns. The per-column share has to stay an
integer: on Python 3 the true-division result is a float, which propagates
into the computed column widths and makes the separator line construction
raise TypeError before anything is printed.

The tests only use the public Framework API (constructor plus table()) and
assert on structural properties of what was printed: identical border lines,
border and data rows of the same width, and the literal text of every cell.
'''

import contextlib
import io
import re
import unittest

from recon.core.framework import Framework

BORDER = re.compile(r'^  \+[-]+\+$')
ROW = re.compile(r'^  \| .* \|$')


class TableTest(unittest.TestCase):

    def render(self, data, header=[], title=''):
        '''Renders one table through the real framework and returns the lines.'''
        framework = Framework('unittest')
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            framework.table(data, header=header, title=title)
        text = buffer.getvalue()
        lines = text.splitlines()
        self.assertTrue(lines, 'table printed nothing')
        return text, lines

    def borders(self, lines):
        return [line for line in lines if BORDER.match(line)]

    def rows(self, lines):
        return [line for line in lines if ROW.match(line)]

    def assert_table_shape(self, lines, expected_borders):
        '''Asserts one consistent border width and equally wide cell rows.'''
        borders = self.borders(lines)
        self.assertEqual(expected_borders, len(borders))
        self.assertEqual(1, len(set(borders)))
        width = len(borders[0])
        rows = self.rows(lines)
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(width, len(row))

    def test_long_title_divisible_by_columns(self):
        # data columns are 1 and 2 wide, header is 1 and 2 wide, so the
        # untitled table needs 6 characters; a 20 character title leaves a
        # surplus of 14, which splits evenly over two columns.
        title = 'Long title over cols'.ljust(20, '.')
        self.assertEqual(20, len(title))
        text, lines = self.render(
            [['c', 'dd']], header=['a', 'bb'], title=title)
        self.assert_table_shape(lines, 4)
        self.assertIn(title, text)
        self.assertGreaterEqual(len(self.borders(lines)[0]), len(title) + 4)
        for cell in ('a', 'bb', 'c', 'dd'):
            self.assertIn(cell, text)

    def test_long_title_with_remainder(self):
        # same columns as above, but a 21 character title leaves a surplus of
        # 15, so the columns cannot share the surplus equally.
        title = 'Long title over cols'.ljust(21, '.')
        self.assertEqual(21, len(title))
        text, lines = self.render(
            [['c', 'dd']], header=['a', 'bb'], title=title)
        self.assert_table_shape(lines, 4)
        self.assertIn(title, text)
        self.assertGreaterEqual(len(self.borders(lines)[0]), len(title) + 4)

    def test_long_title_single_column(self):
        title = 'Single column title'.ljust(19, '.')
        self.assertEqual(19, len(title))
        text, lines = self.render([['abc']], header=['h'], title=title)
        self.assert_table_shape(lines, 4)
        self.assertIn(title, text)
        self.assertIn('abc', text)
        self.assertGreaterEqual(len(self.borders(lines)[0]), len(title) + 4)

    def test_long_title_without_header(self):
        title = 'Title without header'.ljust(20, '.')
        self.assertEqual(20, len(title))
        text, lines = self.render([['aa', 'bbb']], title=title)
        self.assert_table_shape(lines, 3)
        self.assertIn(title, text)
        self.assertIn('bbb', text)
        self.assertNotIn('| aa |', text)

    def test_short_title_control(self):
        # the title is narrower than the data, so no width is shared out.
        text, lines = self.render(
            [['alice', 'example']], header=['user', 'domain'], title='ab')
        self.assert_table_shape(lines, 4)
        self.assertIn('user', text)
        self.assertIn('alice', text)

    def test_no_title_control(self):
        text, lines = self.render([['alice', 'example']], header=['user', 'domain'])
        self.assert_table_shape(lines, 3)
        self.assertIn('alice', text)
        self.assertNotIn('None', text)

    def test_numeric_and_none_values_render(self):
        # None must render as padding, numbers as their text form.
        text, lines = self.render(
            [[None, 42, 3.5]], header=['empty', 'count', 'ratio'], title='Values')
        self.assert_table_shape(lines, 4)
        self.assertIn('42', text)
        self.assertIn('3.5', text)
        self.assertIn('count', text)
        self.assertNotIn('None', text)

    def test_multiple_rows_stay_aligned(self):
        title = 'Many rows under a wide title'.ljust(29, '.')
        self.assertEqual(29, len(title))
        text, lines = self.render(
            [['a', 'b'], ['ccc', 'dddd'], [None, 7]],
            header=['left', 'right'], title=title)
        self.assert_table_shape(lines, 4)
        self.assertIn(title, text)
        self.assertIn('ccc', text)
        self.assertIn('7', text)
        self.assertNotIn('None', text)


if __name__ == '__main__':
    unittest.main()
