import re
from typing import List, Dict, Any
from config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_text(
    pages: List[Dict[str, Any]], 
    chunk_size: int = CHUNK_SIZE, 
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[Dict[str, Any]]:
    """
    Intelligently chunks text across pages with overlap.
    Preserves page numbers, sentence boundaries, and section headers.
    
    Each returned chunk has:
    - chunk_index: int
    - page_number: int
    - section_title: str
    - content: str
    - char_count: int
    """
    chunks = []
    chunk_counter = 0

    for page_info in pages:
        page_num = page_info.get("page_number", 1)
        raw_text = page_info.get("text", "").strip()
        
        if not raw_text:
            continue

        # Normalize multiple spaces & newlines
        cleaned_text = re.sub(r'\r\n', '\n', raw_text)
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        # Split into paragraphs first
        paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]

        current_chunk_text = ""
        current_section = ""

        for para in paragraphs:
            # Detect section title (e.g. # Title or Question Q1 or bold headers)
            header_match = re.match(r'^(?:#+|\*\*|Q\d+|Chapter|Section|Module)\s*(.+)', para)
            if header_match:
                current_section = header_match.group(0)[:80]

            if not current_chunk_text:
                current_chunk_text = para
            elif len(current_chunk_text) + len(para) + 2 <= chunk_size:
                current_chunk_text += "\n\n" + para
            else:
                # Chunk is full, finalize it
                chunks.append({
                    "chunk_index": chunk_counter,
                    "page_number": page_num,
                    "section_title": current_section or f"Page {page_num}",
                    "content": current_chunk_text.strip(),
                    "char_count": len(current_chunk_text)
                })
                chunk_counter += 1

                # Carry over overlap from the end of current_chunk_text
                if chunk_overlap > 0 and len(current_chunk_text) > chunk_overlap:
                    overlap_start = max(0, len(current_chunk_text) - chunk_overlap)
                    # Try to break on whitespace in overlap
                    space_idx = current_chunk_text.find(" ", overlap_start)
                    if space_idx != -1:
                        overlap_text = current_chunk_text[space_idx:].strip()
                    else:
                        overlap_text = current_chunk_text[overlap_start:].strip()
                    current_chunk_text = overlap_text + "\n\n" + para
                else:
                    current_chunk_text = para

        # Add remaining text in page if any
        if current_chunk_text and current_chunk_text.strip():
            chunks.append({
                "chunk_index": chunk_counter,
                "page_number": page_num,
                "section_title": current_section or f"Page {page_num}",
                "content": current_chunk_text.strip(),
                "char_count": len(current_chunk_text)
            })
            chunk_counter += 1

    return chunks
