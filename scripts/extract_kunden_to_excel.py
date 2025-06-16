"""
This script extracts data from structured markdown files (Kunde X.md) located in subdirectories
within a base directory, and compiles this information into an Excel file.
It parses specific fields from each markdown file, including contact information,
and formats the output into a structured table.
"""
import os
import re
import pandas as pd
from phone_formatter import format_phone_number # Import the formatter

def parse_contact_info(contact_section_text):
    """
    Parses the contact information block to extract website, email, and phone.
    Handles both single-line and multi-line (bulleted) formats.
    """
    website, email, phone = None, None, None

    # Try to find on the same line as a potential "Contact Information:" header text (if any was passed)
    # or just generally within the block.
    # Pattern: Key: Value (potentially followed by ; or (Not found) or end of line)
    website_match = re.search(r"Website:\s*([^;\n(]+)", contact_section_text, re.IGNORECASE)
    if website_match and "not found" not in website_match.group(1).lower():
        website = website_match.group(1).strip()

    email_match = re.search(r"Email:\s*([^;\n(]+)", contact_section_text, re.IGNORECASE)
    if email_match and "not found" not in email_match.group(1).lower():
        email = email_match.group(1).strip()

    # Regex to capture more of the phone number, stopping at a clear delimiter or end of common patterns
    phone_pattern = r"Phone:\s*(.*?)(?=\s*;\s*Email:|\s*;\s*Website:|\s*\n\s*\*|\s*\(Email:|\s*\(Website:|\s*\Z)"
    phone_match = re.search(phone_pattern, contact_section_text, re.IGNORECASE | re.DOTALL)
    if phone_match:
        raw_phone = phone_match.group(1).strip()
        if "not found" not in raw_phone.lower():
            phone = format_phone_number(raw_phone) # Apply formatter
    
    # If not all found, or to catch bulleted items specifically
    # Look for bulleted items (multi-line format)
    if not website:
        bullet_website_match = re.search(r"^\s*\*\s*Website:\s*(.*)", contact_section_text, re.IGNORECASE | re.MULTILINE)
        if bullet_website_match and "not found" not in bullet_website_match.group(1).lower():
            website = bullet_website_match.group(1).strip()
    
    if not email:
        bullet_email_match = re.search(r"^\s*\*\s*Email:\s*(.*)", contact_section_text, re.IGNORECASE | re.MULTILINE)
        if bullet_email_match and "not found" not in bullet_email_match.group(1).lower():
            email = bullet_email_match.group(1).strip()

    if not phone: # If not found in single-line style or needs specific bullet parsing
        bullet_phone_match = re.search(r"^\s*\*\s*Phone:\s*(.*)", contact_section_text, re.IGNORECASE | re.MULTILINE)
        if bullet_phone_match:
            raw_phone_bullet = bullet_phone_match.group(1).strip()
            if "not found" not in raw_phone_bullet.lower():
                 phone = format_phone_number(raw_phone_bullet) # Apply formatter
            
    return website, email, phone

def parse_kunde_md(file_path, kunde_identifier):
    """
    Parses a single Kunde X.md file and extracts the required information.
    """
    data = {
        "Company Name": None,
        "Industry": None,
        "Products/Services Offered": None,
        "USP (Unique Selling Proposition) / Key Selling Points": None,
        "Customer Target Segments": None,
        "Business Model": None,
        "Company Size Indicators": None,
        "Innovation Level Indicators": None,
        "Geographic Reach": None,
        "Website": None,
        "Email": None,
        "Phone": None,
        "Source Document Section/Notes": kunde_identifier,
        "Is_Successful_Partner": "TRUE" # Or 1, as per preference
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # General field extraction
        fields_to_extract = [
            "Company Name",
            "Industry",
            "Products/Services Offered",
            "USP (Unique Selling Proposition) / Key Selling Points",
            "Customer Target Segments",
            "Business Model",
            "Company Size Indicators",
            "Innovation Level Indicators",
            "Geographic Reach"
        ]

        for field in fields_to_extract:
            # Regex to find "N.  **`Field Name:`** Value"
            # Anchored to line start, handles multi-line values, stops before next numbered field.
            # The lookahead also considers a potential "Okay, I have processed..." line sometimes found at the end.
            pattern = re.compile(
                r"^\s*(?:\d+\.\s*)?\*\*`" + re.escape(field) +
                r":\`\*\*\s*(.*?)(?=\n\s*\d+\.\s*\*\*`[\w\s()/:.'-]+:`\*\*|\n\s*Okay, I have processed|\Z)",
                re.DOTALL | re.IGNORECASE | re.MULTILINE
            )
            match = pattern.search(content)
            if match:
                value = match.group(1).strip()
                if value.lower() == "not found":
                    data[field] = "" # Empty cell for "Not found"
                else:
                    data[field] = value
            else:
                # Fallback for fields that might not be numbered or have slight variations
                # This is a more general pattern, less strict about numbering.
                fallback_pattern = re.compile(
                    r"\*\*`" + re.escape(field) +
                    r":\`\*\*\s*(.*?)(?=\n\s*\*\*`[\w\s()/:.'-]+:`\*\*|\n\s*Okay, I have processed|\Z)",
                    re.DOTALL | re.IGNORECASE
                )
                fallback_match = fallback_pattern.search(content)
                if fallback_match:
                    value = fallback_match.group(1).strip()
                    if value.lower() == "not found":
                        data[field] = ""
                    else:
                        data[field] = value


        # Contact Information extraction
        # Regex to find the entire "10.  **`Contact Information:`**..." block
        contact_block_pattern = re.compile(
            r"^\s*10\.\s*\*\*`Contact Information:`\*\*\s*(.*?)"+
            r"(?=\n\s*(?:\d+\.\s*)?\*\*`[\w\s()/:.'-]+:`\*\*|\n\s*Okay, I have processed|\Z)", # Lookahead for next field or end
            re.DOTALL | re.IGNORECASE | re.MULTILINE
        )
        contact_block_match = contact_block_pattern.search(content)
        
        if contact_block_match:
            contact_block_text = contact_block_match.group(1).strip()
            website, email, phone = parse_contact_info(contact_block_text)
            data["Website"] = website if website else ""
            data["Email"] = email if email else ""
            data["Phone"] = phone if phone else ""
        else: # Fallback if the "10." numbered pattern for contact info isn't found
            generic_contact_block_pattern = re.compile(
                r"\*\*`Contact Information:`\*\*\s*(.*?)"+
                r"(?=\n\s*(?:\d+\.\s*)?\*\*`[\w\s()/:.'-]+:`\*\*|\n\s*Okay, I have processed|\Z)",
                re.DOTALL | re.IGNORECASE
            )
            generic_contact_block_match = generic_contact_block_pattern.search(content)
            if generic_contact_block_match:
                contact_block_text = generic_contact_block_match.group(1).strip()
                website, email, phone = parse_contact_info(contact_block_text)
                data["Website"] = website if website else ""
                data["Email"] = email if email else ""
                data["Phone"] = phone if phone else ""


    except FileNotFoundError:
        print(f"Error: File not found {file_path}")
        return None
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return None
    
    return data

def main():
    base_dir = "data/Kunde_Structured_Output"
    output_file = "kunden_golden_standard.xlsx"
    all_kunden_data = []

    if not os.path.exists(base_dir):
        print(f"Error: Base directory not found: {base_dir}")
        return

    # Get folder names and sort them numerically
    folder_names = os.listdir(base_dir)
    
    def get_kunde_number(name):
        # Extracts the number from "Kunde X" or "KundeX"
        match = re.search(r'Kunde\s*(\d+)', name, re.IGNORECASE)
        return int(match.group(1)) if match else float('inf')

    sorted_folder_names = sorted(folder_names, key=get_kunde_number)

    for kunde_folder_name in sorted_folder_names:
        kunde_folder_path = os.path.join(base_dir, kunde_folder_name)
        if os.path.isdir(kunde_folder_path):
            # Expecting folder names like "Kunde 1", "Kunde 2", etc.
            # And files like "Kunde 1.md"
            md_file_name = f"{kunde_folder_name}.md"
            md_file_path = os.path.join(kunde_folder_path, md_file_name)

            if os.path.exists(md_file_path):
                print(f"Processing {md_file_path}...")
                extracted_data = parse_kunde_md(md_file_path, kunde_folder_name)
                if extracted_data:
                    all_kunden_data.append(extracted_data)
            else:
                print(f"Warning: Markdown file {md_file_name} not found in {kunde_folder_path}")

    if not all_kunden_data:
        print("No data extracted. Exiting.")
        return

    df = pd.DataFrame(all_kunden_data)
    
    # Ensure correct column order
    column_order = [
        "Company Name", "Industry", "Products/Services Offered",
        "USP (Unique Selling Proposition) / Key Selling Points", "Customer Target Segments",
        "Business Model", "Company Size Indicators", "Innovation Level Indicators",
        "Geographic Reach", "Website", "Email", "Phone",
        "Source Document Section/Notes", "Is_Successful_Partner"
    ]
    df = df[column_order]

    try:
        # Use ExcelWriter to gain access to the workbook and worksheet objects for formatting
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='KundenData')
            
            # Auto-adjust columns' width
            worksheet = writer.sheets['KundenData']
            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter
                for cell in column_cells:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Define the table range
            # The table range will be from A1 to the last column and last row
            # df.shape[0] is number of rows, df.shape[1] is number of columns
            # Add 1 to rows for the header
            # Convert column number to letter for the last column
            from openpyxl.utils import get_column_letter
            last_column_letter = get_column_letter(df.shape[1])
            table_range = f"A1:{last_column_letter}{df.shape[0] + 1}"
            
            # Create a table
            from openpyxl.worksheet.table import Table, TableStyleInfo
            tab = Table(displayName="KundenTable", ref=table_range)
            
            # Add a default style to the table
            style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False,
                                   showLastColumn=False, showRowStripes=True, showColumnStripes=False)
            tab.tableStyleInfo = style
            worksheet.add_table(tab)
                
        print(f"Successfully created Excel file: {output_file}")
    except Exception as e:
        print(f"Error writing to Excel file {output_file}: {e}")

if __name__ == "__main__":
    main()