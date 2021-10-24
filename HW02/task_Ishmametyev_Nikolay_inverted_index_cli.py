from __future__ import annotations

import re
import json
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from collections import defaultdict
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
        """Save Inverted Index in the filepath"""
        with open(filepath, 'w') as fio:
            json.dump(self.index, fio)

    @classmethod
    def load(cls, filepath: str) -> InvertedIndex:
        """Load Inverted Index from filepath"""
        with open(filepath, 'r') as fio:
            index = json.load(fio)
        return InvertedIndex(index)


def load_documents(filepath: str) -> Dict[int, str]:
    documents = {}
    with open(filepath) as fio:
        lines = fio.readlines()
        for line in lines:
            doc_id, content = line.lower().split("\t", 1)
            documents[int(doc_id)] = content.strip()
    return documents


def build_inverted_index(documents: Dict[int, str]) -> InvertedIndex:
    index = defaultdict(list)
    for key, content in documents.items():
        words = re.split(r"\W+", content)
        for word in set(words):
            if word not in index or key not in index[word]:
                index[word].append(key)
    return InvertedIndex(index)


def callback_build(arguments):
    documents = load_documents(arguments.dataset)
    inverted_index = build_inverted_index(documents)
    if arguments.strategy == 'pickle':
        raise NotImplementedError('Pickle policy not implemented yet')

    inverted_index.dump(arguments.output)


def callback_query(arguments):
    inverted_index = InvertedIndex.load(arguments.json_index)
    for words in arguments.query:
        res = inverted_index.query(words)
        _print_for_everest(res)


def _print_for_everest(arr: List):
    arr_str = [str(el) for el in arr]
    print(','.join(arr_str))


def setup_parser(parser: ArgumentParser):
    """Parsing of CLI arguments

    A couple of branches to choose:
    - build: build Inverted index
    - query: load Inverted index and query it with words
    """
    subparsers = parser.add_subparsers(help='Choose command')

    parser_build = subparsers.add_parser('build', help='Build inverted index with documents',
                                         formatter_class=ArgumentDefaultsHelpFormatter)

    parser_build.add_argument('-d', '--dataset', required=True)
    parser_build.add_argument('-o', '--output', required=True)
    parser_build.add_argument('-s', '--strategy', default='json', choices=['json', 'pickle'])
    parser_build.set_defaults(callback=callback_build)

    parser_query = subparsers.add_parser('query', help='Query inverted index with words',
                                         formatter_class=ArgumentDefaultsHelpFormatter)
    parser_query.add_argument('--json-index', required=True, help='Path to JSON inverted index')
    parser_query.add_argument('--query', nargs='+', action='append', metavar='WORD')
    parser_query.set_defaults(callback=callback_query)


def main():
    parser = ArgumentParser(prog='Inverted Index CLI',
                            description='Lib to build, load, dump and query Inverted Index')
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()
