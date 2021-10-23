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

  def testQueryText(self):
    result = self.expense.Query('拉麵')
    self.assertEqual(_GetIdList(result.expenses), ['1', '7', '8'])

  def testQueryAnd(self):
    result = self.expense.Query('label:拉麵 amount>=285')
    self.assertEqual(_GetIdList(result.expenses), ['1', '7'])

  """
  def testQueryNot(self):
    result = self.expense.Query('-東門 =amount>=250')
    self.assertEqual(_GetIdList(result.expenses), ['4', '6', '8'])

  def testQueryOr(self):
    result = self.expense.Query('東門 OR amount>=500')
    self.assertEqual(_GetIdList(result.expenses), ['2', '3', '5'])

  def testQueryParenthesis(self):
    result = self.expense.Query('(拉麵 OR amount>=500) date>2020-06-25')
    self.assertEqual(_GetIdList(result.expenses), ['5', '7', '8'])
  """

  def testTotalAmount(self):
    total_amount = self.expense.TotalAmount()
    self.assertEqual(total_amount, 2300)


if __name__ == '__main__':
  unittest.main()
