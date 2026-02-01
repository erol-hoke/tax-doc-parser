from docling.document_converter import DocumentConverter
from pathlib import Path
import json

class TaxDocumentParser:
    def __init__(self):
        self.converter = DocumentConverter()
    
    def parse_document(self, file_path: str) -> dict:
        """Parse a document and return structured content."""
        result = self.converter.convert(file_path)
        
        return {
            "markdown": result.document.export_to_markdown(),
            "tables": self._extract_tables(result),
            "text": result.document.export_to_text(),
            "metadata": {
                "filename": Path(file_path).name,
                "pages": len(result.document.pages) if hasattr(result.document, 'pages') else 1
            }
        }
    
    def _extract_tables(self, result) -> list:
        """Extract all tables from the document."""
        tables = []
        for idx, table in enumerate(result.document.tables):
            df = table.export_to_dataframe()
            tables.append({
                "index": idx,
                "data": df.to_dict('records'),
                "html": table.export_to_html()
            })
        return tables