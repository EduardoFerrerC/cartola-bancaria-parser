import pandas as pd


def generate_excel(transactions, file_name):
    """Generate an Excel file from a list of transactions."""
    # Create a DataFrame from the transactions
    df = pd.DataFrame(transactions)
    
    # Write the DataFrame to an Excel file
    df.to_excel(file_name, index=False)
    
    print(f'Excel file {file_name} generated successfully.')


# Example usage:
# transactions = [{'date': '2021-01-01', 'amount': 100, 'description': 'Payment'}, {'date': '2021-01-02', 'amount': -50, 'description': 'Refund'}]
# generate_excel(transactions, 'transactions.xlsx')