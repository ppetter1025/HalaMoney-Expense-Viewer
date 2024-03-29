#!/usr/bin/env python3

import unittest

import csv

from cli import Expense
from cli import QueryHelper
from cli import Tokenize

def _GetIdList(result):
  return [entry['Id'] for entry in result]

class TokenizeTest(unittest.TestCase):

  def testTokenize(self):
    self.assertEqual(
        Tokenize('  -(拉麵 OR amount>=500) OR (date>2020-06-25)  --amount>=100'),
        ['-(拉麵 OR amount>=500)', 'OR', '(date>2020-06-25)', '--amount>=100'])

  def testTokenizeInvalidParentheses(self):
    with self.assertRaises(ValueError):
      Tokenize('( () ')
    with self.assertRaises(ValueError):
      Tokenize('( )) ')

  def testTokenizeEmptyStr(self):
    self.assertEqual(Tokenize(''), [])


class ExpenseTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.exp1 = Expense([
      {'Id': '1'},
      {'Id': '2'},
      {'Id': '3'},
    ])
    cls.exp2 = Expense([
      {'Id': '2'},
      {'Id': '3'},
      {'Id': '4'},
    ])
    with open('expense.csv', 'r') as fp:
      cls.expense = Expense(list(csv.DictReader(fp)))

  def testIntersection(self):
    self.assertEqual(
        [entry['Id'] for entry in self.exp1.Intersection(self.exp2).expenses],
        ['2', '3'])

  def testIntersectionUniversalSet(self):
    universal_expense = Expense(Expense.UNIVERSAL_SET)
    self.assertEqual(self.expense.Intersection(universal_expense),
                     self.expense)
    self.assertEqual(universal_expense.Intersection(self.expense),
                     self.expense)

  def testIntersectionEmptySet(self):
    empty_expense = Expense([])
    self.assertEqual(self.expense.Intersection(empty_expense).expenses,
                     [])
    self.assertEqual(empty_expense.Intersection(self.expense).expenses,
                     [])

  def testUnion(self):
    self.assertEqual(
        [entry['Id'] for entry in self.exp1.Union(self.exp2).expenses],
        ['1', '2', '3', '4'])

  def testUnionUniversalSet(self):
    universal_expense = Expense(Expense.UNIVERSAL_SET)
    self.assertEqual(self.expense.Union(universal_expense).expenses,
                     Expense.UNIVERSAL_SET)
    self.assertEqual(universal_expense.Union(self.expense).expenses,
                     Expense.UNIVERSAL_SET)

  def testUnionEmptySet(self):
    empty_expense = Expense([])
    self.assertEqual(self.expense.Union(empty_expense).expenses,
                     self.expense.expenses)
    self.assertEqual(empty_expense.Union(self.expense).expenses,
                     self.expense.expenses)

  def testTotalAmount(self):
    total_amount = self.expense.TotalAmount()
    self.assertEqual(total_amount, 2300)

class QueryHelperTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.helper = QueryHelper()
    with open('expense.csv', 'r') as fp:
      cls.expense = Expense(list(csv.DictReader(fp)))

  def _QueryTestHelper(self, query, expected_ids):
    result = self.helper.Query(self.expense, query)
    self.assertEqual(_GetIdList(result.expenses), expected_ids)

  def testQueryEmpty(self):
    self._QueryTestHelper('', [str(i+1) for i in range(8)])

  def testQueryText(self):
    self._QueryTestHelper('拉麵', ['1', '7', '8'])

  def testQueryAnd(self):
    self._QueryTestHelper('label:拉麵 amount>=285', ['1', '7'])

  def testQueryNot(self):
    self._QueryTestHelper('-東門 -amount>=250', ['4', '6', '8'])

  def testQueryDoubleNot(self):
    self._QueryTestHelper('--拉麵', ['1', '7', '8'])

  def testQueryNotWithParenthesis(self):
    self._QueryTestHelper('-(amount>=200 食)', ['2', '3', '4', '5'])

  def testQueryMultipleParentheses(self):
    self._QueryTestHelper('(((-東門 -amount>=250)))', ['4', '6', '8'])

  def testQueryOr(self):
    self._QueryTestHelper('東門 OR amount>=500', ['2', '3', '5'])

  def testQueryOrWithParenthesis(self):
    self._QueryTestHelper('東門 OR amount>=500', ['2', '3', '5'])


if __name__ == '__main__':
  unittest.main()
