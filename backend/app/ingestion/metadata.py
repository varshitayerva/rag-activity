from typing import Dict, Any, Optional
from datetime import datetime


class MetadataExtractor:
    @staticmethod
    def extract(
        filename: str,
        file_type: str,
        page_count: int,
        department: Optional[str] = None,
        category: Optional[str] = None,
        extra_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        metadata = {
            "filename": filename,
            "file_type": file_type,
            "page_count": page_count,
            "department": department or "General",
            "category": category or "Uncategorized",
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        if extra_metadata:
            metadata.update(extra_metadata)

        return metadata
