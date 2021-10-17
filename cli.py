#!/usr/bin/env python3

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
  s.strip()
  if s == '':
    return []

  if s[0] == '(':
    # Find matching parenthesis
    cnt = 1
    for i in range(1, len(s)):
      if s[i] == '(':
        cnt += 1
      if s[i] == ')':
        cnt -= 1
      if cnt == 0:
        return [s[:i+1]] + Tokenize(s[i+2:])
    raise ValueError('Failed to parse the query')

  splitted = s.split(' ', 1)
  if len(splitted) == 1:
    return splitted
  return splitted[:1] + Tokenize(splitted[1])

class Expense:

  def __init__(self, expenses: list):
    assert isinstance(expenses, list)
    self.expenses = expenses

  def QueryAllFields(self, subquery):
    return_list = []
    for expense in self.expenses:
      for field, value in expense.items():
        if subquery in value:
          return_list += [expense]
          break
    return return_list

  def QueryField(self, field, op, field_query):
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
    for expense in self.expenses:
      if hit(field, op, field_query, expense[FIELD_MAPPING[field]]):
        return_list += [expense]

    return return_list

  def QueryOne(self, query):
    # Check >=, <= before >, <
    field_operators = [':', '>=', '<=', '<', '>']
    for op in field_operators:
      if op in query:
        query = query.replace(op, ' ')
        assert len(query.split()) == 2
        field, field_query = query.split(' ', 1)
        return self.QueryField(field, op, field_query)

    return self.QueryAllFields(query)

  def Query(self, query):

    def Union(exp1, exp2):
      return list(set(exp1.expenses).union(set(exp2.expenses)))

    def Intersection(exp1, exp2):
      if exp1 is None or exp2 is None:
        return exp1 if exp2 is None else exp2
      return Expense([value for value in exp1.expenses if value in exp2.expenses])

    tokens = Tokenize(query)
    if tokens == []:
        return self

    if len(tokens) == 1:
      return Expense(self.QueryOne(tokens[0]))

    # Use None as universal set.
    result = None
    for token in tokens:
      result = Intersection(result, self.Query(token))

    return result

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


def main():
  parser = argparse.ArgumentParser(epilog='Supported keywords: %r' % list(FIELD_MAPPING.keys()))
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

  if args.base_query is not None:
    base_expenses = all_expenses.Query(args.base_query)
  else:
    base_expenses = all_expenses

  base_expenses.Query(args.query).Output(base_expenses.TotalAmount())


if __name__ == '__main__':
  main()
