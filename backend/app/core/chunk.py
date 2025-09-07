import logging
import re
from typing import List, Dict, Tuple
import tiktoken
from app.core.settings import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """Handle intelligent text chunking with heading awareness and overlap"""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text into overlapping segments with heading awareness
        
        Args:
            text: Input text to chunk
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of chunk dictionaries with content, metadata, and token counts
        """
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Identify headings and structure
            structured_sections = self._identify_sections(processed_text)
            
            # Create chunks respecting section boundaries
            chunks = self._create_chunks(structured_sections, metadata)
            
            logger.info(f"Created {len(chunks)} chunks from text")
            return chunks
            
        except Exception as e:
            logger.error(f"Text chunking failed: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text for chunking"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove page numbers and headers/footers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Page \d+ of \d+$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def _identify_sections(self, text: str) -> List[Dict]:
        """Identify document sections and headings"""
        sections = []
        lines = text.split('\n')
        current_section = {'heading': '', 'content': '', 'level': 0}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect headings (various formats)
            heading_match = self._detect_heading(line)
            
            if heading_match:
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section.copy())
                
                # Start new section
                current_section = {
                    'heading': heading_match['text'],
                    'content': line + '\n',
                    'level': heading_match['level']
                }
            else:
                # Add to current section
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _detect_heading(self, line: str) -> Dict:
        """Detect if a line is a heading and return its level"""
        # Markdown-style headings
        md_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if md_match:
            return {
                'text': md_match.group(2).strip(),
                'level': len(md_match.group(1))
            }
        
        # Numbered headings (1., 1.1, 1.1.1, etc.)
        numbered_match = re.match(r'^(\d+(?:\.\d+)*)\.?\s+(.+)$', line)
        if numbered_match:
            level = len(numbered_match.group(1).split('.'))
            return {
                'text': numbered_match.group(2).strip(),
                'level': level
            }
        
        # ALL CAPS headings (likely titles)
        if line.isupper() and len(line) > 3 and len(line) < 100:
            return {
                'text': line.title(),
                'level': 1
            }
        
        # Title case headings (short lines that look like titles)
        if (line.istitle() and 
            len(line) < 100 and 
            not line.endswith('.') and 
            not line.endswith(':') and
            len(line.split()) <= 10):
            return {
                'text': line,
                'level': 2
            }
        
        return None
    
    def _create_chunks(self, sections: List[Dict], metadata: Dict = None) -> List[Dict]:
        """Create chunks from sections with proper overlap"""
        chunks = []
        chunk_index = 0
        
        for section in sections:
            section_text = section['content']
            section_tokens = len(self.encoding.encode(section_text))
            
            # If section is small enough, keep it as one chunk
            if section_tokens <= self.chunk_size:
                chunk = {
                    'chunk_index': chunk_index,
                    'content': section_text.strip(),
                    'heading': section['heading'],
                    'level': section['level'],
                    'token_count': section_tokens,
                    'metadata': metadata or {}
                }
                chunks.append(chunk)
                chunk_index += 1
            else:
                # Split large section into multiple chunks
                section_chunks = self._split_section(section, chunk_index, metadata)
                chunks.extend(section_chunks)
                chunk_index += len(section_chunks)
        
        return chunks
    
    def _split_section(self, section: Dict, start_index: int, metadata: Dict = None) -> List[Dict]:
        """Split a large section into multiple chunks with overlap"""
        text = section['content']
        chunks = []
        
        # Split by sentences first
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        current_tokens = 0
        chunk_index = start_index
        
        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))
            
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunk = {
                    'chunk_index': chunk_index,
                    'content': current_chunk.strip(),
                    'heading': section['heading'],
                    'level': section['level'],
                    'token_count': current_tokens,
                    'metadata': metadata or {}
                }
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                current_chunk = self._create_overlap(current_chunk) + sentence
                current_tokens = len(self.encoding.encode(current_chunk))
            else:
                current_chunk += sentence
                current_tokens += sentence_tokens
        
        # Add final chunk if it has content
        if current_chunk.strip():
            chunk = {
                'chunk_index': chunk_index,
                'content': current_chunk.strip(),
                'heading': section['heading'],
                'level': section['level'],
                'token_count': current_tokens,
                'metadata': metadata or {}
            }
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - could be improved with NLTK or spaCy
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_overlap(self, text: str) -> str:
        """Create overlap from the end of a chunk"""
        # Take the last portion of text for overlap
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= self.chunk_overlap:
            return text + " "
        
        # Take last chunk_overlap tokens
        overlap_tokens = tokens[-self.chunk_overlap:]
        overlap_text = self.encoding.decode(overlap_tokens)
        
        return overlap_text + " "
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
