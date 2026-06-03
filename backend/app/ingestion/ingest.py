"""Document ingestion with automatic vectorization."""

import os
from pathlib import Path
from typing import List, Optional
from backend.app.ingestion.parser import get_parser
from backend.app.ingestion.chunker import FixedChunker
from backend.app.database.postgres import db_client
from backend.app.search.vector_store import vector_store


class DocumentIngester:
    """Ingest documents and automatically create embeddings."""

    def __init__(self):
        self.chunker = FixedChunker(chunk_size=500, overlap=100)

    def ingest_file(
        self,
        file_path: str,
        filename: Optional[str] = None
    ) -> dict:
        """Ingest a single file and create embeddings."""

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if filename is None:
            filename = os.path.basename(file_path)

        file_size = os.path.getsize(file_path)
        file_ext = Path(file_path).suffix.lower().strip('.')

        # Parse file
        print(f"Parsing {filename}...")
        with open(file_path, 'rb') as f:
            file_content = f.read()

        try:
            parser = get_parser(file_ext)
            text, page_count, metadata = parser.parse(file_content)
        except Exception as e:
            print(f"❌ Failed to parse {filename}: {e}")
            return {"error": str(e)}

        # Create chunks
        print(f"Creating chunks...")
        chunks = self.chunker.chunk(text)

        # Save to database
        print(f"Saving to database...")
        doc_id = db_client.add_document(filename, file_ext, file_size)

        chunk_list = []
        for i, chunk in enumerate(chunks):
            chunk_list.append({
                'chunk_index': i,
                'text': chunk,
                'section': None,
                'page_number': None
            })

        db_client.add_chunks(doc_id, chunk_list)

        # Create embeddings and add to vector store
        print(f"Creating embeddings for {len(chunk_list)} chunks...")
        texts = [c['text'] for c in chunk_list]

        chunk_metadata = [
            {
                'chunk_id': i,
                'text': c['text'],
                'doc_id': doc_id,
                'document_name': filename,
            }
            for i, c in enumerate(chunk_list)
        ]

        vector_store.add(texts, chunk_metadata)

        result = {
            "success": True,
            "doc_id": doc_id,
            "filename": filename,
            "file_size": file_size,
            "chunks_created": len(chunks),
            "embeddings_created": len(chunk_metadata)
        }

        print(f"✅ Ingestion complete for {filename}")
        print(f"   Document ID: {doc_id}")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Vector store size: {vector_store.size()}")

        return result

    def ingest_directory(
        self,
        directory: str,
        extensions: List[str] = None
    ) -> dict:
        """Ingest all files in a directory."""

        if extensions is None:
            extensions = ['pdf', 'txt', 'md', 'docx']

        if not os.path.isdir(directory):
            raise NotADirectoryError(f"Directory not found: {directory}")

        results = []
        for file_path in Path(directory).iterdir():
            if file_path.is_file():
                ext = file_path.suffix.lower().strip('.')
                if ext in extensions:
                    try:
                        result = self.ingest_file(str(file_path))
                        results.append(result)
                    except Exception as e:
                        print(f"❌ Failed to ingest {file_path.name}: {e}")

        return {
            "total_files": len(results),
            "successful": len([r for r in results if r.get("success")]),
            "results": results
        }


# Convenience function
def ingest(file_path: str, filename: Optional[str] = None) -> dict:
    """Ingest a document."""
    ingester = DocumentIngester()
    return ingester.ingest_file(file_path, filename)
