import pandas as pd


def generate_excel(data, file_path):
    """Generates a formatted Excel file from the provided data."""
    # Create a Pandas DataFrame from the data
    df = pd.DataFrame(data)

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Sheet1', index=False)

        # Get the xlsxwriter workbook and worksheet objects.
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Set the column width to make the data easier to read.
        worksheet.set_column('A:Z', 20)

        # Add some cell formats.
        header_format = workbook.add_format({'bold': True, 'bg_color': '#FFA07A', 'border': 1})
        cell_format = workbook.add_format({'border': 1})

        # Apply the formats to the header row and all cells.
        worksheet.set_row(0, None, header_format)
        worksheet.conditional_format('A1:Z100', {'type': 'no_blanks', 'format': cell_format})
    
    print(f"Excel file generated: {file_path}")


# Example usage:
# generate_excel([{'Column1': 'Data1', 'Column2': 'Data2'}], 'output.xlsx')
