from __future__ import annotations

import re
import json
from typing import Dict, List


class InvertedIndex:
    def __init__(self, index: Dict[str, List[int]]):
        self.index = index

    def __eq__(self, other):
        if set(self.index.keys()) != set(other.index.keys()):
            return False
        for key, value in self.index.items():
            if sorted(value) != sorted(other.index[key]):
                return False
        return True

    def query(self, words: List[str]) -> List[int]:
        """Return the list of relevant documents for the given query"""
        if not words:
            return []
        words_dict = {}
        for word in words:
            if word in self.index:
                words_dict[word] = self.index[word]
            else:
                return []

        possible = set(words_dict[words[0]])
        for word in words[1:]:
            possible = possible.intersection(set(words_dict[word]))
        return list(possible)

    def dump(self, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump(self.index, f)

    @classmethod
    def load(cls, filepath: str) -> InvertedIndex:
        with open(filepath, 'r') as f:
            index = json.load(f)
        return InvertedIndex(index)


def load_documents(filepath: str) -> Dict[int, str]:
    documents = {}
    with open(filepath) as f:
        lines = f.readlines()
        for line in lines:
            doc_id, content = line.lower().split("\t", 1)
            documents[int(doc_id)] = content.strip()
    return documents


def build_inverted_index(documents: Dict[int, str]) -> InvertedIndex:
    index = {}
    for key, content in documents.items():
        words = re.split(r"\W+", content)
        for word in set(words):
            if word not in index:
                index[word] = [key]
            else:
                if key not in index[word]:
                    index[word].append(key)
    return InvertedIndex(index)


def main():
    documents = load_documents("text.txt")
    inverted_index = build_inverted_index(documents)
    inverted_index.dump("inverted.index")
    inverted_index = InvertedIndex.load("inverted.index")
    document_ids = inverted_index.query(["two", "words"])


if __name__ == "__main__":
    main()
