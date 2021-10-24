#!/usr/bin/env python3

import unittest

import csv

from cli import Expense
from cli import Tokenize

def _GetIdList(result):
  return [entry['Id'] for entry in result]

class TokenizeTest(unittest.TestCase):

  def testTokenize(self):
    self.assertEqual(Tokenize('(拉麵 OR amount>=500) OR date>2020-06-25'),
        ['(拉麵 OR amount>=500)', 'OR', 'date>2020-06-25'])

  def testTokenizeEmptyStr(self):
    self.assertEqual(Tokenize(''), [])

class ExpenseTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    with open('expense.csv', 'r') as fp:
      cls.expense = Expense(list(csv.DictReader(fp)))

  def _QueryTestHelper(self, query, expected_ids):
    result = self.expense.Query(query)
    self.assertEqual(_GetIdList(result.expenses), expected_ids)

  def testQueryText(self):
    self._QueryTestHelper('拉麵', ['1', '7', '8'])

  def testQueryAnd(self):
    self._QueryTestHelper('label:拉麵 amount>=285', ['1', '7'])

  def testQueryNot(self):
    self._QueryTestHelper('-東門 -amount>=250', ['4', '6', '8'])

  """
  def testQueryNotWithParenthesis(self):
    self._QueryTestHelper('-(amount>=200 食)', ['2', '3', '4', '5'])

  def testQueryMultipleParenthesis(self):
    self._QueryTestHelper('(((-東門 -amount>=250)))', ['4', '6', '8'])

  def testQueryOr(self):
    self._QueryTestHelper('東門 OR amount>=500', ['2', '3', '5'])

  def testQueryOrWithParenthesis(self):
    self._QueryTestHelper('東門 OR amount>=500', ['2', '3', '5'])
  """

  def testTotalAmount(self):
    total_amount = self.expense.TotalAmount()
    self.assertEqual(total_amount, 2300)


if __name__ == '__main__':
  unittest.main()
