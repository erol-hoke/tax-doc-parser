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

INSTRUCTIONS:
1. Extract ONLY the requested fields
2. If a field is not found, use null
3. For monetary values, include only the number (no $ or commas)
4. For dates, use YYYY-MM-DD format
5. Return ONLY valid JSON with the field names as keys

Return your response as a JSON object."""