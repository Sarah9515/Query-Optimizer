import re
import oracledb
from itertools import combinations
from flask import Flask, render_template, request
import joblib
from Indexes_Optimizer import IndexQueryOptimizer, extract_values_from_index_statements
from IN_Clause import extract_and_filter,separate_column_values, extract_table_names


app = Flask(__name__)

oracle_connection_string = 'your_username/your_password@better-sql.francecentral.cloudapp.azure.com/FREE'
connection = oracledb.connect(oracle_connection_string)
cursor = connection.cursor()


class QueryConditions:
    def __init__(self, column_values, other_conditions=None):
        self.column_values = column_values
        self.other_conditions = other_conditions or []

    def to_sql_query(self, table_name):
        conditions = []

        for column, values in self.column_values.items():
            conditions.append(f"{table_name}.{column} IN ({', '.join(map(repr, values))})")

        conditions_str = " AND ".join(conditions)
        conditions_str = f"({conditions_str}) AND {' AND '.join(self.other_conditions)}" if self.other_conditions else conditions_str

        return f"SELECT * FROM {table_name} WHERE {conditions_str}"
    
    def to_delete_sql_query(self, table_name):
        conditions = []

        for column, values in self.column_values.items():
            conditions.append(f"{table_name}.{column} IN ({', '.join(map(repr, values))})")

        conditions_str = " AND ".join(conditions)
        conditions_str = f"({conditions_str}) AND {' AND '.join(self.other_conditions)}" if self.other_conditions else conditions_str

        return f"DELETE * FROM {table_name} WHERE {conditions_str}"

def extract_columns(query):
    # Use regular expression to find columns part after SELECT/DELETE keyword
    match = re.search(r'(SELECT|DELETE)\s+(?P<columns>.*?)\s+FROM', query, re.IGNORECASE)
    
    if match:
        columns_str = match.group('columns')
        # Split columns string by commas and remove leading/trailing whitespaces
        columns = [col.strip() for col in columns_str.split(',')]
        return columns
    else:
        return None


def optimize_query_with_in(original_query, column_values, table_name, columns):
    query_type = original_query.split()[0].upper()

    if query_type == 'SELECT':
        # Extract the JOIN, conditions, and ORDER BY clause from the original query
        join_index = original_query.find("JOIN")
        where_index = original_query.find("WHERE")
        order_by_index = original_query.find("ORDER BY")

        join_clause = original_query[join_index:where_index].strip() if join_index != -1 else ""
        conditions = original_query[where_index+5:order_by_index].strip() if where_index != -1 else ""
        order_by_clause = original_query[order_by_index:].strip() if order_by_index != -1 else ""

    elif query_type == 'DELETE':
        # Extract the conditions from the original DELETE query
        where_index = original_query.find("WHERE")
        conditions = original_query[where_index+5:].strip() if where_index != -1 else ""

    # Create a set to store unique conditions
    unique_conditions = set()

    # Process existing conditions and add them to the set
    for condition in conditions.split("AND"):
        condition = condition.strip()
        if not any(col in condition for col in column_values):
            unique_conditions.add(condition)

    # Create an optimized query using the IN clause for each specified column
    for column, values in column_values.items():
        in_clause = f"{table_name}.{column} IN ({', '.join(map(repr, values))})"
        unique_conditions.add(in_clause)

    # Combine conditions into a string
    optimized_conditions_str = " AND ".join(unique_conditions)

    # Combine optimized query with JOIN, conditions, and ORDER BY (for SELECT) or WHERE (for DELETE)
    if query_type == 'SELECT':
        if columns:
            column_str = ', '.join(columns)
            optimized_query = f"SELECT {column_str} FROM {table_name} {join_clause} WHERE {optimized_conditions_str} {order_by_clause}"
        else:
            optimized_query = f"SELECT * FROM {table_name} {join_clause} WHERE {optimized_conditions_str} {order_by_clause}"
    elif query_type == 'DELETE':
        if columns:
            column_str = ', '.join(columns)
            optimized_query = f"DELETE {column_str} FROM {table_name} WHERE {optimized_conditions_str}"
        else:
            optimized_query = f"DELETE * FROM {table_name} WHERE {optimized_conditions_str}"

    return optimized_query

def extract_first_word(query):
    return query.split()[0].upper()

def extract_table_name(query):
    match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
    if match:
        return match.group(1)
    else:
        return None

def generate_index_combinations(columns, table_name):
    index_combinations = []

    for i in range(1, len(columns) + 1):
        for subset in combinations(columns, i):
            index_combination = f"INDEX({table_name} {', '.join(subset)})"
            index_combinations.append(index_combination)

    return index_combinations

def generate_query_with_indexes(original_query, index_combinations):
    first_word = extract_first_word(original_query)

    return [
        f"{first_word} /*+ {indexes} */ {original_query[len(first_word):].rstrip(';').lstrip()}"
        for indexes in index_combinations
    ]


def test(user_input_query, combined_list=None):
    
    expressions = extract_and_filter(user_input_query)
    column_values_to_optimize = separate_column_values(expressions)
    columns = extract_columns(user_input_query)

    # Convert QueryConditions to SQL query
    table_name = extract_table_names(user_input_query)
    optimized_query = optimize_query_with_in(user_input_query, column_values_to_optimize, table_name, columns)
    optimized_query1 = optimized_query.split(' ; ')
    output = [query.rstrip(';') for query in optimized_query1]



    user_input_query1 = user_input_query.split(' ; ')
    user_input_query2 = [query.rstrip(';') for query in user_input_query1]

    index_optimizer = IndexQueryOptimizer(user_input_query)
    suggested_indexes = index_optimizer.optimize_query()
    suggested_indexes = extract_values_from_index_statements(suggested_indexes)

    # Table Name
    table_name = extract_table_name(user_input_query)

    new_queries = []  # Initialize new_queries outside the if block

    if table_name:
        # Generate index combinations
        index_combinations = generate_index_combinations(suggested_indexes, table_name)

        # Generate new queries with indexes
        new_queries = generate_query_with_indexes(user_input_query, index_combinations)


    query_list = new_queries
    expressions_list = []
    column_values_list = []
    columns_list = []
    optimized_queries_list = []

    for input_query in query_list:
          expressions1 = extract_and_filter(input_query)
          column_values_to_optimize1 = separate_column_values(expressions1)
          columns1 = extract_columns(input_query)

          # Convert QueryConditions to SQL query
          table_name1 = extract_table_names(input_query)
          optimized_query_1 = optimize_query_with_in(input_query, column_values_to_optimize1, table_name1, columns1)
          optimized_query_2 = optimized_query_1.split(' ; ')
          optimized_queries1 = [query.rstrip(';') for query in optimized_query_2]

          expressions_list.append(expressions1)
          column_values_list.append(column_values_to_optimize1)
          columns_list.append(columns1)
          optimized_queries_list.extend(optimized_queries1)


    combined_list = []
    combined_list.extend(user_input_query2)
    combined_list.extend(output)
    combined_list.extend(new_queries)
    combined_list.extend(optimized_queries_list)
    
    return combined_list


def predict_execution_time(user_input_query, combined_list):

    result = test(user_input_query, combined_list)

    # Load the pre-trained model and vectorizer
    model = joblib.load('ml-model/linear_regression_model.joblib')
    vectorizer = joblib.load('ml-model/tfidf_vectorizer.joblib')

    # New queries for prediction
    new_queries = result

    # Vectorize the new queries
    new_queries_vectorized = vectorizer.transform(new_queries)

    # Use the model to predict execution time for new queries
    predictions = model.predict(new_queries_vectorized)

    # Return a list of tuples containing each query and its associated execution time
    return list(zip(new_queries, predictions))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input_query = request.form.get('user_input_query')

        # Assuming 'test' function returns the query to execute
        query_to_execute = test(user_input_query)

        # Use the predict_execution_time function
        results = predict_execution_time(user_input_query, query_to_execute)

        # Find the query with the minimum predicted execution time
        min_query, min_time = min(results, key=lambda x: x[1])

        try:
            # Execute the query
            cursor.execute(min_query)
            
            # Fetch the query results
            min_query_results = cursor.fetchall()

            # Prepare data for rendering in HTML
            query_results = [
                {'query': query, 'predicted_execution_time': execution_time}
                for query, execution_time in results
            ]

            min_query_results_html = [
                ', '.join(map(str, result)) for result in min_query_results
            ]

            return render_template(
                'index.html',
                min_query_results=min_query_results_html,
                query_results=query_results,
                min_query=min_query,
                min_time=min_time
            )

        except Exception as e:
            # Handle any errors that may occur during query execution
            return render_template('index.html', error_message=str(e))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
