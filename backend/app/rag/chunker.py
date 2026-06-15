from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """
    Splits raw text into overlapping chunks.

    Why overlap? So context at chunk boundaries isn't lost.
    512 tokens ~ 1 paragraph. Good balance for code + prose.
    RecursiveCharacterTextSplitter tries to split on paragraphs
    first, then sentences, then words — keeps semantic units intact.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_text(text)