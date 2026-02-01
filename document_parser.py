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

        print(f"OCR enabled: {pipeline_options.do_ocr}")
        print(f"   Table structure enabled: {pipeline_options.do_table_structure}")
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )
        print("✅ DocumentConverter initialized with OCR")
    
    def parse_document(self, file_path: str) -> dict:
        """Parse a document and return structured content."""
        print(f"📄 Parsing: {file_path}")
        result = self.converter.convert(file_path)

        markdown = result.document.export_to_markdown()
        text_items = []
        if hasattr(result.document, 'texts'):
            for item in result.document.texts:
                if item.text:
                    text_items.append(item.text)
        
        all_text = "\n".join(text_items)
        
        print(f"   Markdown length: {len(markdown)}")
        print(f"   Text items found: {len(text_items)}")
        print(f"   First 200 chars: {all_text[:200] if all_text else markdown[:200]}")
        
        # Use text_items if markdown just shows images
        final_output = all_text if all_text else markdown
        
        return {
            "markdown": final_output,
            "tables": self._extract_tables(result),
            "text": all_text,
            "metadata": {"filename": Path(file_path).name}
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