import ollama
import json
from typing import List, Dict, Any

class TaxDataExtractor:
    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self.client = ollama.Client()
    
    def extract_fields(
        self, 
        document_text: str, 
        fields_to_extract: List[str],
        document_type: str = "tax document"
    ) -> Dict[str, Any]:
        """Extract specified fields from document text using local LLM."""
        
        prompt = self._build_extraction_prompt(
            document_text, 
            fields_to_extract,
            document_type
        )
        
        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format="json"
        )
        
        try:
            extracted = json.loads(response['message']['content'])
            return extracted
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw": response['message']['content']}
    
    def _build_extraction_prompt(
        self, 
        text: str, 
        fields: List[str],
        doc_type: str
    ) -> str:
        fields_list = "\n".join([f"- {field}" for field in fields])
        
        return f"""You are a tax document data extraction assistant. 
Extract the following fields from this {doc_type}.

FIELDS TO EXTRACT:
{fields_list}

DOCUMENT TEXT:
{text}

CRITICAL RULES:
- ONLY extract values that are EXPLICITLY written in the document
- If a value is not clearly present, you MUST return null
- DO NOT guess, calculate, or infer any values
- DO NOT make up dates, numbers, or names
- Copy values EXACTLY as they appear (including formatting)
- For dates: copy exactly as shown (e.g., "06 April 2024" not reformatted)
- For money: copy exactly as shown (e.g., "£1,234.56" or "1234.56")

Return your response as a JSON object."""