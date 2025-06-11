import os
import re
import logging
import pathlib
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# --- Configuration ---
SOURCE_DOC_PATH = pathlib.Path("../docs/Manuav Kundenzusammenfassung für Klaus.md")
PROMPT_TEMPLATE_PATH = pathlib.Path("../prompts/data_extraction.md")
OUTPUT_BASE_DIR = pathlib.Path("../data/Kunde_Structured_Output") # Updated base output directory
PROCESSED_MD_FILENAME_TEMPLATE = "Kunde {kunde_num}.md"
RAW_PROMPT_FILENAME_TEMPLATE = "prompt_Kunde_{kunde_num}.txt"
RAW_LLM_RESPONSE_FILENAME_TEMPLATE = "llm_response_Kunde_{kunde_num}.txt"
GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY" # Corrected to be the var name, not a key itself
GEMINI_MODEL_NAME = "gemini-2.5-pro-preview-05-06" # Updated model name
START_KUNDE_NUM = 1 # Reset to process full range
END_KUNDE_NUM = 70

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_prompt_template(file_path: pathlib.Path) -> str | None:
    """Loads the prompt template from the given file path."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading prompt template file {file_path}: {e}")
        return None

def parse_company_data(file_path: pathlib.Path) -> dict[int, str]:
    """
    Parses the source document to extract text for each company.
    Returns a dictionary mapping company number to its raw text.
    """
    company_texts = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to find "KUNDE X: ..." and capture X and the text until the next "KUNDE Y:" or end of file.
        # This regex assumes "KUNDE X:" is at the beginning of a line.
        # It captures the Kunde number and the text block associated with it.
        # The (?s) flag makes . match newlines.
        # The lookahead (?=(?:^KUNDE \d+:|\Z)) ensures we capture text until the next Kunde or EOF.
        pattern = re.compile(r"^KUNDE\s*(\d+):.*?$(.*?)(?=(?:^KUNDE\s*\d+:|\Z))", re.MULTILINE | re.DOTALL)
        
        matches = pattern.findall(content)
        
        for match in matches:
            try:
                kunde_num_str, text_block = match
                kunde_num = int(kunde_num_str)
                # Clean up the text block: strip leading/trailing whitespace
                # and potentially the "KUNDE X: CompanyName.com" line itself if it's part of text_block
                # For now, let's assume the text_block is what comes *after* the KUNDE X: line.
                # The regex above might need adjustment based on exact file structure.
                # Let's refine the regex to better capture only the content *after* the KUNDE X line.
            except ValueError:
                logger.warning(f"Could not parse Kunde number from match: {match[0]}")
                continue

        # Refined approach: Find all "KUNDE X:" lines, then extract text between them.
        # This is often more robust for varying content lengths.
        
        # Find all "KUNDE X:" lines with their start positions, case-insensitively
        kunde_starts = []
        for match_obj in re.finditer(r"^KUNDE\s*(\d+):", content, re.MULTILINE | re.IGNORECASE):
            kunde_num = int(match_obj.group(1))
            start_index = match_obj.end() # Position right after "KUNDE X:"
            kunde_starts.append({'num': kunde_num, 'start_index': start_index, 'match_start': match_obj.start()})

        if not kunde_starts:
            logger.error(f"No 'KUNDE X:' sections found in {file_path}")
            return {}

        # Sort by match start position to ensure correct order
        kunde_starts.sort(key=lambda x: x['match_start'])

        for i, kunde_info in enumerate(kunde_starts):
            kunde_num = kunde_info['num']
            text_start_index = kunde_info['start_index']
            
            if i + 1 < len(kunde_starts):
                # Text ends at the start of the next "KUNDE" section
                text_end_index = kunde_starts[i+1]['match_start']
            else:
                # Last Kunde section, text goes to the end of the file
                text_end_index = len(content)
            
            company_text = content[text_start_index:text_end_index].strip()
            company_texts[kunde_num] = company_text
            
    except FileNotFoundError:
        logger.error(f"Source document not found: {file_path}")
    except Exception as e:
        logger.error(f"Error parsing source document {file_path}: {e}")
    return company_texts

def call_gemini_api(company_text: str, api_key: str, prompt_template: str) -> tuple[str | None, str | None]:
    """
    Calls the Gemini API with the company text and prompt template.
    Returns a tuple: (raw_llm_text_response, final_prompt_sent_to_llm).
    Returns (None, final_prompt) if API error after prompt construction.
    Returns (None, None) if error before prompt construction (e.g. API key).
    """
    final_prompt = None # Initialize in case of early exit
    if not api_key:
        logger.error("Gemini API key not provided or found in environment.")
        return None, None

    try:
        # Replace placeholder in the prompt template
        # The placeholder was identified as "[PASTE GERMAN TEXT FOR ONE COMPANY HERE]"
        # from prompts/data_extraction.md
        final_prompt = prompt_template.replace("[PASTE GERMAN TEXT FOR ONE COMPANY HERE]", company_text)
        
        genai.configure(api_key=api_key)  # type: ignore
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)  # type: ignore
        
        generation_config = GenerationConfig(
            temperature=1.0
            # Other parameters like top_p, top_k, max_output_tokens will use defaults
        )
        
        response = model.generate_content(
            final_prompt,
            generation_config=generation_config,
        )
        
        raw_llm_text_response = None
        if response.parts:
            raw_llm_text_response = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        elif hasattr(response, 'text') and response.text:
             raw_llm_text_response = response.text
        
        if raw_llm_text_response is None:
            logger.warning(f"Gemini API response for a company did not contain expected text parts. Response: {response}")
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                logger.error(f"Prompt blocked. Reason: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}")
        
        return raw_llm_text_response, final_prompt

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        logger.error(f"Error details: {str(e)}")
        return None, final_prompt # Return final_prompt if it was constructed

def main():
    """Main function to orchestrate the data extraction and processing."""
    logger.info("Starting company data processing script.")
    
    api_key = os.getenv(GEMINI_API_KEY_ENV_VAR)
    if not api_key:
        logger.error(f"Environment variable {GEMINI_API_KEY_ENV_VAR} not set. Exiting.")
        return

    prompt_template = load_prompt_template(PROMPT_TEMPLATE_PATH)
    if not prompt_template:
        logger.error("Failed to load prompt template. Exiting.")
        return

    all_company_data = parse_company_data(SOURCE_DOC_PATH)
    if not all_company_data:
        logger.error("Failed to parse company data from source document. Exiting.")
        return

    # Ensure base output directory exists
    if not OUTPUT_BASE_DIR.exists():
        try:
            OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured base output directory exists: {OUTPUT_BASE_DIR}")
        except Exception as e:
            logger.error(f"Could not create base output directory {OUTPUT_BASE_DIR}: {e}. Exiting.")
            return
            
    processed_count = 0
    for kunde_num in range(START_KUNDE_NUM, END_KUNDE_NUM + 1):
        logger.info(f"--- Processing Kunde {kunde_num} ---")
        
        # Create specific output directory for this Kunde
        kunde_specific_output_dir = OUTPUT_BASE_DIR / f"Kunde {kunde_num}"
        try:
            kunde_specific_output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create directory {kunde_specific_output_dir} for Kunde {kunde_num}: {e}. Skipping.")
            continue

        company_text = all_company_data.get(kunde_num)
        
        if not company_text:
            logger.warning(f"Data for Kunde {kunde_num} not found in the parsed source document. Skipping.")
            continue
            
        logger.info(f"Found data for Kunde {kunde_num}. Length: {len(company_text)} chars.")

        raw_llm_response_text, final_llm_prompt = call_gemini_api(company_text, api_key, prompt_template)
        
        # Save raw prompt
        if final_llm_prompt:
            prompt_file_name = RAW_PROMPT_FILENAME_TEMPLATE.format(kunde_num=kunde_num)
            prompt_file_path = kunde_specific_output_dir / prompt_file_name
            try:
                with open(prompt_file_path, 'w', encoding='utf-8') as f:
                    f.write(final_llm_prompt)
                logger.info(f"Saved raw prompt for Kunde {kunde_num} to {prompt_file_path}")
            except Exception as e:
                logger.error(f"Error writing raw prompt file {prompt_file_path} for Kunde {kunde_num}: {e}")

        # Save raw LLM response and processed MD
        if raw_llm_response_text:
            # Save raw LLM response
            llm_response_file_name = RAW_LLM_RESPONSE_FILENAME_TEMPLATE.format(kunde_num=kunde_num)
            llm_response_file_path = kunde_specific_output_dir / llm_response_file_name
            try:
                with open(llm_response_file_path, 'w', encoding='utf-8') as f:
                    f.write(raw_llm_response_text)
                logger.info(f"Saved raw LLM response for Kunde {kunde_num} to {llm_response_file_path}")
            except Exception as e:
                logger.error(f"Error writing raw LLM response file {llm_response_file_path} for Kunde {kunde_num}: {e}")

            # Save processed MD (which is the same as raw_llm_response_text in this case)
            processed_md_file_name = PROCESSED_MD_FILENAME_TEMPLATE.format(kunde_num=kunde_num)
            processed_md_file_path = kunde_specific_output_dir / processed_md_file_name
            try:
                with open(processed_md_file_path, 'w', encoding='utf-8') as f:
                    f.write(raw_llm_response_text)
                logger.info(f"Successfully wrote processed MD for Kunde {kunde_num} to {processed_md_file_path}")
                processed_count += 1
            except Exception as e:
                logger.error(f"Error writing processed MD file {processed_md_file_path} for Kunde {kunde_num}: {e}")
        else:
            logger.error(f"Failed to get API response text for Kunde {kunde_num}. Skipping file writes for LLM output.")
            
    logger.info(f"--- Script Finished ---")
    logger.info(f"Processed {processed_count} companies from Kunde {START_KUNDE_NUM} to {END_KUNDE_NUM}.")

if __name__ == "__main__":
    main()