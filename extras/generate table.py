import os


def list_csv_row_counts(folder_path):
    print(f"{'File Name':<40} | {'Total Lines':>15}")
    print("-" * 58)

    # Ensure the folder exists
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return

    # Loop through all files in the directory
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.csv'):
            file_path = os.path.join(folder_path, filename)

            try:
                # Open and count lines efficiently
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    row_count = sum(1 for _ in file)
            except Exception as e:
                row_count = "Error reading"

            # Truncate long filenames with '...' so they fit the table
            display_name = filename if len(filename) <= 40 else filename[:37] + "..."

            print(f"{display_name:<40} | {row_count:>15}")


# --- How to use it ---
# Replace 'your_folder_path_here' with the actual path to your folder
# Example for Windows: r"C:\Users\Name\Documents\Data"
# Example for Mac/Linux: "/Users/Name/Documents/Data"

folder = "./generated_files/database_csv"  # "." checks the current folder where the script is saved
list_csv_row_counts(folder)