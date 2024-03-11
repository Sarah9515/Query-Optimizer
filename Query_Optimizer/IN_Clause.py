import re

def extract_and_filter(query):
    # Extract expressions within parentheses
    expressions = re.findall(r'\((.*?)\)', query)

    # Extract all unique column names from the query
    all_column_names = set(re.findall(r'\b(\w+\.\w+)\b', query))

    # Filter expressions based on specified conditions
    filtered_expressions = []
    for expr in expressions:
        if 'OR' in expr:
            sides = [side.strip() for side in expr.split('OR')]
            if len(sides) == 2:
                left_column, right_column = map(lambda s: re.search(r'\b(\w+\.\w+)\b', s).group(1), sides)
                if left_column == right_column and left_column in all_column_names:
                    filtered_expressions.append(expr)

    return filtered_expressions

def separate_column_values(query_list):
    column_values = {}

    for query in query_list:
        # Use regex to find column names and values in the query
        matches = re.findall(r'(\w+)\.(\w+)\s*=\s*\'?(\w+|[\d.]+)\'?', query)

        # Extracting column names and values from matches
        for match in matches:
            table, column, value = match
            if value.isdigit():
                value = int(value)
            elif re.match(r'^\d+\.\d+$', value):
                value = float(value)
            column_values.setdefault(column, []).append(value)

    return column_values


def extract_table_names(query):
    # Extract all table names from the query
    table_names = list(set(re.findall(r'\b(?:FROM|JOIN)\s+(\w+)\b', query, flags=re.IGNORECASE)))

    # Join the table names with commas
    table_names_csv = ', '.join(table_names)

    return table_names_csv


'''
query = "SELECT * FROM products WHERE (products.brand = 'Apple' OR products.brand = 'Samsung') AND (products.price = 'Apple' OR products.hh < 145) AND (emp.solde = 400 OR emp.solde = 145)"


result = extract_and_filter(query)
print(result)

result2 = extract_columns(result)
print(result2)

result3 = separate_column_values(result)
print(result3)

table_names = extract_table_names(result)
print(table_names)

'''