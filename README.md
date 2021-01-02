# HalaMoney Expense Viewer

## Introduction
[HalaMoney](https://halamoney.weebly.com/) is a expense tracking (記帳) app on iOS and Android platform.
Its most appealing feature to me is that it can add custom label to my expenses, which is easy for future queries.

This tool is a simple CLI tool to query expenses exported from HalaMoney app.

## Usage
```
usage: cli.py [-h] -q QUERY [-b BASE_QUERY] [-i INPUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -q QUERY, --query QUERY
                        Query string
  -b BASE_QUERY, --base-query BASE_QUERY
                        Base query string
  -i INPUT_FILE, --input INPUT_FILE
                        Path to the expense CSV file. Read from STDIN if not
                        given
```

This query will return all expenses which contains "三餐" substring:

```
./cli.py -i expense.csv -q "三餐"
```

The tool returns the intersection of the queries if multiple queries are given separated by spaces.
For example, this query will return all expenses before "2020/06/27" in label "拉麵":

```
./cli.py -i expense.csv -q "label:拉麵 date<2020/06/27"
```

`BASE_QUERY` is an optional argument to caculate the how much proportion the queried expenses accounts for.
For example, this query will calculated the proportion of "三餐" before "2020/06/27":

```
./cli.py -i expense.csv -q "三餐" -b "date<2020/06/27"
```

## Future work

- Supports parentheses and OR in the query
- A frontend web UI
