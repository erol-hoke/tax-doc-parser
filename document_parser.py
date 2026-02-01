from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from pathlib import Path
import json

print("🔥 LOADING DOCUMENT_PARSER.PY WITH OCR ENABLED 🔥")

class TaxDocumentParser:
    def __init__(self):
        # Configure pipeline with OCR enabled
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )
    
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
        tables = []
        if hasattr(result.document, 'tables'):
            for idx, table in enumerate(result.document.tables):
                try:
                    df = table.export_to_dataframe()
                    tables.append({
                        "index": idx,
                        "data": df.to_dict('records'),
                    })
                except Exception:
                    pass
        return tables