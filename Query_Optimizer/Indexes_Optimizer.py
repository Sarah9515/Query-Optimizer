import re

class IndexQueryOptimizer:
    def __init__(self, original_query):
        self.original_query = original_query

    def optimize_query(self):
        conditions = self.extract_conditions()
        selected_columns = self.extract_selected_columns()
        suggested_indexes = self.suggest_indexes(conditions, selected_columns)
        return suggested_indexes

    def extract_conditions(self):
        conditions = re.findall(r'\(([^)]+?)\)', self.original_query)
        return [condition.strip() for condition in conditions]

    def extract_selected_columns(self):
        # Extract columns from the SELECT or DELETE statement
        select_match = re.search(r'(?:SELECT|DELETE)\s+(.*?)\s+FROM', self.original_query, re.IGNORECASE)
        if select_match:
            columns_str = select_match.group(1)
            columns = re.findall(r'(\w+)', columns_str)
            return columns
        else:
            return []

    def extract_columns(self, condition):
        columns = re.findall(r'(\w+)\s*([=<>!]+)', condition)
        return [(col[0], col[1]) for col in columns]

    def suggest_indexes(self, conditions, selected_columns):
        suggested_indexes = set()  # Use a set to avoid duplicate indexes

        # Include existing logic for extracting indexes from conditions
        for condition in conditions:
            columns = self.extract_columns(condition)
            for col, op in columns:
                index_name = f"idx_{col}"
                if op == '=':
                    suggested_indexes.add(f"CREATE INDEX {index_name} ON your_table_name ({col});")
                elif op in ('<', '>', '<=', '>='):
                    suggested_indexes.add(f"CREATE INDEX {index_name}_range ON your_table_name ({col});")
                else:
                    suggested_indexes.add(f"CREATE INDEX {index_name}_non_eq ON your_table_name ({col});")

        # Include new logic to extract columns from the SELECT statement
        for col in selected_columns:
            index_name = f"idx_{col}"
            suggested_indexes.add(f"CREATE INDEX {index_name} ON your_table_name ({col});")

        listt = list(suggested_indexes)
        return listt
    

def extract_values_from_index_statements(suggested_indexes):
    index_names = set()

    for statement in suggested_indexes:
        match = re.search(r'CREATE INDEX (\w+)', statement)
        if match:
            index_name = match.group(1)
            index_names.add(index_name)

    return list(index_names)



