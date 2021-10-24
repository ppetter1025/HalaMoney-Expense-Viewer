#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import datetime
import logging
import sys

FIELD_MAPPING = {
    'id': 'Id',
    'date': '日期',
    'major_component': '主分類',
    'minor_component': '子分類',
    'amount': '該幣別金額',
    'description': '帳務說明',
    'label': '標籤',
}

FIELD_DISPLAY_NAME = {
    'id': 'Id',
    'date': '日期',
    'major_component': '主分類',
    'minor_component': '子分類',
    'amount': '金額',
    'description': '帳務說明',
    'label': '標籤',
}

DEFAULT_FIELD_LENGTH = {
    'id': 5,
    'date': 12,
    'major_component': 8,
    'minor_component': 10,
    'amount': 10,
    'description': 40,
    'label': 39,
}

DEFAULT_FIELD_ORDER = [
    'id',
    'date',
    'major_component',
    'minor_component',
    'amount',
    'description',
    'label',
]

COMPARABLE_FIELDS = [
    'id',
    'date',
    'amount'
]

def Tokenize(s):
  s = s.strip()
  if s == '':
    return []

  cnt = 0
  for i in range(len(s)):
    if s[i] == '(':
      cnt += 1
    if s[i] == ')':
      cnt -= 1
    if cnt < 0:
      raise ValueError('Too many right parentheses.')
    if s[i] == ' ' and cnt == 0:
      return [s[:i]] + Tokenize(s[i+1:])
      continue
  else:
    if cnt > 0:
      raise ValueError('Missing right parentheses.')
    return [s]

class Expense:
  UNIVERSAL_SET = '__UNIVERSAL_SET__'

  def __init__(self, expenses):
    assert isinstance(expenses, list) or expenses == self.UNIVERSAL_SET
    self.expenses = expenses

  def Union(self, exp) -> Expense:
    # Cleaner union implementation.
    exp1, exp2 = self.expenses, exp.expenses
    if (self.expenses == self.UNIVERSAL_SET or
        exp.expenses == self.UNIVERSAL_SET):
      return Expense(self.UNIVERSAL_SET)

    i, j = 0, 0
    ret = []
    while i < len(exp1) and j < len(exp2):
      if exp1[i]['Id'] == exp2[j]['Id']:
        ret += [exp1[i]]
        i += 1
        j += 1
      elif exp1[i]['Id'] < exp2[j]['Id']:
        ret += [exp1[i]]
        i += 1
      else:
        ret += [exp2[j]]
        j += 1
    ret += exp1[i:]
    ret += exp2[j:]

    return Expense(ret)

  def Intersection(self, exp):
    if (self.expenses == self.UNIVERSAL_SET or
        exp.expenses == self.UNIVERSAL_SET):
      return self if exp.expenses == self.UNIVERSAL_SET else exp
    return Expense(
        [value for value in self.expenses if value in exp.expenses])

  def TotalAmount(self):
    return sum([int(expense[FIELD_MAPPING['amount']]) for expense in
      self.expenses])

  def Output(self, base_total_amount=None):
    def FormatPrint(s, l, padding_character=' '):
      num_of_spaces = l - 2*len(s) + sum([len(c.encode()) != 3 for c in s])
      # Replace the newline characters
      s = s.replace('\n', ' ')
      print(s, end=padding_character*num_of_spaces)

    def PrintDashLine():
      for field in DEFAULT_FIELD_ORDER:
        FormatPrint('-', DEFAULT_FIELD_LENGTH[field], '-')
      print('')

    for field in DEFAULT_FIELD_ORDER:
      FormatPrint(FIELD_DISPLAY_NAME[field], DEFAULT_FIELD_LENGTH[field])
    print('')
    PrintDashLine()
    for expense in self.expenses:
      for field in DEFAULT_FIELD_ORDER:
        FormatPrint(expense[FIELD_MAPPING[field]], DEFAULT_FIELD_LENGTH[field])
      print('')

    PrintDashLine()
    print('總金額：%d' % self.TotalAmount(), end='')
    if base_total_amount is not None and base_total_amount != 0:
      print(', 佔全部比例 %.2f%%' % (100.0*self.TotalAmount()/base_total_amount))

class QueryHelper:

  def _FindAllFields(self, expenses, subquery) -> list:
    return_list = []
    for expense in expenses.expenses:
      for field, value in expense.items():
        if subquery in value:
          return_list += [expense]
          break
    return return_list

  def _FindOneField(self, expenses, field, op, field_query) -> list:
    def hit(field, op, field_query, value):
      if op == ':':
        return field_query in value

      if field not in COMPARABLE_FIELDS:
        logging.error('Uncomparable field: %s', field)
        raise ValueError('Field %s is not comparable.', field)

      if field == 'date':
        field_query = datetime.datetime.fromisoformat(
            field_query.replace('/', '-'))
        value = datetime.datetime.fromisoformat(value.replace('/', '-'))
      else:
        value = int(value)
        field_query = int(field_query)
      if op == '<':
        return value < field_query
      if op == '>':
        return value > field_query
      if op == '<=':
        return value <= field_query
      if op == '>=':
        return value >= field_query

      assert False

    return_list = []
    for expense in expenses.expenses:
      if hit(field, op, field_query, expense[FIELD_MAPPING[field]]):
        return_list += [expense]

    return return_list

  def _QueryOneToken(self, expenses, query) -> Expense:
    if query.startswith('-'):
      return self._GetComplementSet(self._QueryOneToken(expenses, query[1:]),
                                    expenses)

    if query.startswith('('):
      assert query[-1] == ')'
      return self.Query(expenses, query[1:-1])

    # Check >=, <= before >, <
    field_operators = [':', '>=', '<=', '<', '>']
    for op in field_operators:
      if op in query:
        query = query.replace(op, ' ')
        assert len(query.split()) == 2
        field, field_query = query.split(' ', 1)
        result = Expense(self._FindOneField(expenses, field, op, field_query))
        break
    else:
      result = Expense(self._FindAllFields(expenses, query))

    return result

  def _GetComplementSet(self, subset, expenses) -> Expense:
    return Expense(
        [exp for exp in expenses.expenses if exp not in subset.expenses])

  def Query(self, expenses, query) -> Expense:
    """
    Not rigorous definition:
      query  := <token> <query> | <token> OR <query> | <token>
      token  := (<query>) | -<token> | <value> | <field><op><value>
      field  := 'id' | 'date' | 'major_component' | 'minor_component' |
                'amount' | 'description' | 'label'
      value  := \w+
      op     := : | > | < | >= | <=
    """

    tokens = Tokenize(query)
    if tokens == []:
        return expenses

    if len(tokens) == 1:
      return self._QueryOneToken(expenses, tokens[0])

    tmp = Expense(Expense.UNIVERSAL_SET)
    intersected_expenses = []
    for token in tokens:
      if token == 'OR':
        if tmp.expenses == Expense.UNIVERSAL_SET:
          raise ValueError('Invalid query.')

        intersected_expenses += [tmp]
        tmp = Expense(Expense.UNIVERSAL_SET)
      else:
        tmp = tmp.Intersection(self._QueryOneToken(expenses, token))

    intersected_expenses += [tmp]

    result = Expense([])
    for exp in intersected_expenses:
      result = result.Union(exp)

    return result


def main():
  parser = argparse.ArgumentParser(
      epilog='Supported keywords: %r' % list(FIELD_MAPPING.keys()))
  parser.add_argument('-q', '--query', dest='query', type=str, default='',
                      help='Query string')
  parser.add_argument('-b', '--base-query', dest='base_query',
                      help='Base query string')
  parser.add_argument('-i', '--input', dest='input_file', default=None,
                      help='Path to the expense CSV file.  Read from STDIN if '
                           'not given')

  args = parser.parse_args()

  if args.input_file is None:
    csv_file_fp = sys.stdin
  else:
    csv_file_fp = open(args.input_file, 'r')

  all_expenses = Expense(list(csv.DictReader(csv_file_fp)))
  helper = QueryHelper()

  if args.base_query is not None:
    base_expenses = helper.Query(all_expenses, args.base_query)
  else:
    base_expenses = all_expenses

  helper.Query(base_expenses, args.query).Output(base_expenses.TotalAmount())


if __name__ == '__main__':
  main()
