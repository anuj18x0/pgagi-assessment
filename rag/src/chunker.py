from typing import List, Dict, Any

class RecursiveChunker:
    def __init__(
        self, 
        chunk_size: int = 512, 
        chunk_overlap: int = 64,
        separators: List[str] = ["\n\n", "\n", ". ", " ", ""]
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators

    def split_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        """
        chunks = self._recursive_split(text, self.separators)
        
        final_chunks = []
        for i, chunk_text in enumerate(chunks):
            # Create a copy of metadata and add specific chunk info
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            
            final_chunks.append({
                "text": chunk_text.strip(),
                "metadata": chunk_metadata
            })
            
        return final_chunks

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Implementation of recursive character splitting.
        """
        final_chunks = []
        
        # Get the current separator
        separator = separators[0] if separators else ""
        new_separators = separators[1:] if len(separators) > 1 else []
        
        # Split the text by the current separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
            
        good_splits = []
        for s in splits:
            if len(s) <= self.chunk_size:
                good_splits.append(s)
            else:
                # If a split is still too large, merge existing good splits and recurse on the large one
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                
                # Recurse
                recursion_result = self._recursive_split(s, new_separators)
                final_chunks.extend(recursion_result)
        
        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)
            
        return final_chunks

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """
        Merge small splits into chunks of roughly chunk_size with overlap.
        """
        docs = []
        current_doc = []
        total_len = 0
        
        for s in splits:
            len_s = len(s)
            
            # If adding this split exceeds chunk_size
            if total_len + len_s + (len(separator) if current_doc else 0) > self.chunk_size:
                if total_len > 0:
                    doc = separator.join(current_doc)
                    docs.append(doc)
                    
                    # Handle overlap: keep last few splits that fit in chunk_overlap
                    overlap_doc = []
                    overlap_len = 0
                    for split in reversed(current_doc):
                        if overlap_len + len(split) + (len(separator) if overlap_doc else 0) <= self.chunk_overlap:
                            overlap_doc.insert(0, split)
                            overlap_len += len(split) + len(separator)
                        else:
                            break
                    current_doc = overlap_doc
                    total_len = overlap_len
            
            current_doc.append(s)
            total_len += len_s + (len(separator) if len(current_doc) > 1 else 0)
            
        if current_doc:
            docs.append(separator.join(current_doc))
            
        return docs
