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
    'date',
]

class Expense:
  def __init__(self, expenses=None):
    if isinstance(expenses, list):
      self.expenses = expenses
    else:
      self.expenses = list(csv.DictReader(expenses))

  def QueryAll(self, subquery):
    return_list = []
    for expense in self.expenses:
      for field, value in expense.items():
        if subquery in value:
          return_list += [expense]
    return return_list

  def QueryField(self, field, op, field_query):
    def hit(field, op, field_query, value):
      if field == 'date':
        field_query = datetime.datetime.fromisoformat(field_query.replace('/', '-'))
        value = datetime.datetime.fromisoformat(value.replace('/', '-'))

      if op == '<':
        return value < field_query
      if op == '>':
        return value > field_query
      
      assert False

    return_list = []
    if op == ':':
      for expense in self.expenses:
        if field_query in expense[FIELD_MAPPING[field]]:
          return_list += [expense]
    else:
      if field not in COMPARABLE_FIELDS:
        logging.error('Uncomparable field: %s', field)
      
      for expense in self.expenses:
        if hit(field, op, field_query, expense[FIELD_MAPPING[field]]):
          return_list += [expense]

    return return_list

  def Query(self, query):
    def Intersection(lst1, lst2):
      return [value for value in lst1 if value in lst2]

    result = None
    field_operators = [':', '<', '>']
    for subquery in query.split():
      field = None
      for op in field_operators:
        if op in subquery:
          field, field_query = subquery.split(op, 1)
          subquery_res = self.QueryField(field, op, field_query)
          break
      else:
        subquery_res = self.QueryAll(subquery)

      if result is None:
        result = subquery_res
      else:
        result = Intersection(result, subquery_res)

    return Expense(result)
  
  def TotalAmount(self):
    return sum([int(expense[FIELD_MAPPING['amount']]) for expense in self.expenses])
  
  def Output(self, base_total_amount=None):
    def FormatPrint(s, l, padding_character=' '):
      num_of_spaces = l - 2*len(s) + sum([len(c.encode()) != 3 for c in s]) 
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
    if base_total_amount is not None:
      print(', 佔全部比例 %.2f%%' % (100.0*self.TotalAmount()/base_total_amount))


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-q', '--query', dest='query', type=str, required=True,
                      help='Query string')
  parser.add_argument('-b', '--base-query', dest='base_query',
                      help='Base query string')
  parser.add_argument('-i', '--input', dest='input_file', default=None,
                      help='Path to the expense CSV file.  Read from STDIN if not given')

  args = parser.parse_args()

  if args.input_file is None:
    csv_file = sys.stdin
  else:
    csv_file = open(args.input_file, 'r')

  all_expenses = Expense(csv_file)

  if args.base_query is not None:
    base_expenses = all_expenses.Query(args.base_query)
  else:
    base_expenses = all_expenses

  base_expenses.Query(args.query).Output(base_expenses.TotalAmount())


main()
