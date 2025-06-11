import os
import pandas as pd
from dotenv import load_dotenv
import re
import json
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel

def get_gemini_response(prompt):
    """
    Sends a prompt to the Gemini API and returns the response.
    """
    model = GenerativeModel('gemini-2.5-pro-preview-06-05')
    response = model.generate_content(prompt)
    return response.text

def extract_german_text(file_path):
    """
    Extracts the German text from the prompt file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'--- GERMAN COMPANY TEXT BELOW ---(.*)--- END OF GERMAN COMPANY TEXT ---', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def parse_kunde_range(range_str):
    """Parses the KUNDE_RANGE string (e.g., '1-5') into a start and end integer."""
    try:
        start, end = map(int, range_str.split('-'))
        return start, end
    except ValueError:
        raise ValueError("Invalid KUNDE_RANGE format. Please use 'start-end', e.g., '1-70'.")

def main():
    """
    Main function to generate company descriptions.
    """
    # Construct paths relative to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

    # Configure API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    configure(api_key=api_key)

    # Create output directory
    output_dir = os.path.join(project_root, 'description_output')
    os.makedirs(output_dir, exist_ok=True)

    # Load the Excel file
    excel_path = os.path.join(project_root, 'kunden_golden_standard.xlsx')
    df = pd.read_excel(excel_path)

    # Parse Kunde range
    range_str = os.getenv("KUNDE_RANGE", f"1-{len(df)}")
    start_kunde, end_kunde = parse_kunde_range(range_str)

    results = []

    # Loop through the specified range of Kunden
    for kunde_number in range(start_kunde, end_kunde + 1):
        # Adjust for 0-based index of the dataframe
        df_index = kunde_number - 1
        if df_index < 0 or df_index >= len(df):
            print(f"Kunde number {kunde_number} is out of the dataframe's range. Skipping.")
            continue
        
        row_data = df.loc[df_index]
        company_name = row_data['Company Name']
        excel_data_str = row_data.to_string() # Convert the row to a string format

        prompt_file_path = os.path.join(project_root, 'data', 'Kunde_Structured_Output', f'Kunde {kunde_number}', f'prompt_Kunde_{kunde_number}.txt')

        if os.path.exists(prompt_file_path):
            german_text = extract_german_text(prompt_file_path)
            if german_text:
                with open(os.path.join(project_root, 'prompts', 'company_description_prompt.txt'), 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
                prompt = prompt_template.format(excel_data=excel_data_str, german_text=german_text)
                
                # Save the request
                with open(os.path.join(output_dir, f'Kunde_{kunde_number}_request.txt'), 'w', encoding='utf-8') as f:
                    f.write(prompt)

                raw_response = get_gemini_response(prompt)

                # Save the raw response
                with open(os.path.join(output_dir, f'Kunde_{kunde_number}_response.txt'), 'w', encoding='utf-8') as f:
                    f.write(raw_response)

                # Clean and parse the JSON
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:].strip()
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3].strip()
                
                try:
                    description_data = json.loads(cleaned_response)
                    description = description_data.get("summary", "")
                except json.JSONDecodeError:
                    print(f"Could not decode JSON for {company_name}. Saving raw response.")
                    description = raw_response # Fallback to raw response

                results.append({'name': company_name, 'description': description})
                print(f"Generated description for {company_name} (Kunde {kunde_number})")
            else:
                print(f"Could not extract German text from {prompt_file_path}")
        else:
            print(f"Prompt file not found for {company_name} at {prompt_file_path}")

    # Save the results to a CSV file
    output_df = pd.DataFrame(results)
    output_csv_path = os.path.join(project_root, 'company_descriptions.csv')
    output_df.to_csv(output_csv_path, index=False)
    print(f"Successfully generated company descriptions and saved to {output_csv_path}")

if __name__ == "__main__":
    main()