from __future__ import annotations

import re
import json
import sys
from io import TextIOWrapper
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType, ArgumentTypeError
from collections import defaultdict
from struct import pack, unpack, calcsize
from typing import Dict, List


class EncodedFileType(FileType):
    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                stdin = TextIOWrapper(sys.stdin.buffer, encoding=self._encoding)
                return stdin
            elif 'w' in self._mode:
                stdout = TextIOWrapper(sys.stdout.buffer, encoding=self._encoding)
                return stdout
            else:
                msg = 'argument "-" with mode %r' % self._mode
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as e:
            message = "can't open '%s': %s"
            raise ArgumentTypeError(message % (string, e))


class StoragePolicy:
    byte_order = '>'
    header_len_fmt_str = f'{byte_order} I'
    header_fmt_str = '{byte_order} {header_length}s'
    docs_fmt_str = '{byte_order} {docs_length}H'

    @staticmethod
    def dump(word_to_docs_mapping: Dict, filepath: str) -> None:
        pass

    @staticmethod
    def load(filepath: str) -> InvertedIndex:
        pass


class JSONStoragePolicy(StoragePolicy):
    @staticmethod
    def dump(word_to_docs_mapping: Dict, filepath: str) -> None:
        """Save Inverted Index in the filepath"""
        with open(filepath, 'w') as fio:
            json.dump(word_to_docs_mapping, fio)

    @classmethod
    def load(cls, filepath: str) -> InvertedIndex:
        """Load Inverted Index from filepath"""
        with open(filepath, 'r') as fio:
            index = json.load(fio)
        return InvertedIndex(index)


class StructStoragePolicy(StoragePolicy):
    byte_order = '>'
    header_len_fmt_str = f'{byte_order} I'
    header_fmt_str = '{byte_order} {header_length}I'
    docs_fmt_str = '{byte_order} {docs_length}H'

    @staticmethod
    def dump(word_to_docs_mapping: Dict, filepath: str) -> None:
        """Save Inverted Index in the filepath"""
        with open(filepath, 'wb') as fio:
            pairs, all_docs_ids = [], []
            for word, doc_ids in word_to_docs_mapping.items():
                pairs.append((word, len(doc_ids)))
                all_docs_ids.extend(doc_ids)
            header = json.dumps(pairs).encode('utf-8')
            fio.write(pack(StoragePolicy.header_len_fmt_str, len(header)))
            fio.write(pack(StoragePolicy.header_fmt_str.format(byte_order=StoragePolicy.byte_order,
                                                               header_length=len(header)), header))
            fio.write(pack(StoragePolicy.docs_fmt_str.format(byte_order=StoragePolicy.byte_order,
                                                             docs_length=len(all_docs_ids)), *all_docs_ids))

    @classmethod
    def load(cls, filepath: str) -> InvertedIndex:
        """Load Inverted Index from filepath"""
        with open(filepath, 'rb') as fio:
            bytes = fio.read()

        # Load size of header
        meta_bytes_length = calcsize(StoragePolicy.header_len_fmt_str)
        header_length, = unpack(StoragePolicy.header_len_fmt_str, bytes[:meta_bytes_length])

        # Load header
        header_fmt = StoragePolicy.header_fmt_str.format(byte_order=StoragePolicy.byte_order,
                                                         header_length=header_length)
        header_bytes_length = calcsize(header_fmt)
        code_points, = unpack(header_fmt,
                              bytes[meta_bytes_length:meta_bytes_length + header_bytes_length])
        pairs = json.loads(code_points.decode('utf8'))

        # Load documents
        index = {}
        start_pos = meta_bytes_length + header_bytes_length
        for word, n_docs in pairs:
            docs_fmt = StoragePolicy.docs_fmt_str.format(byte_order=StoragePolicy.byte_order,
                                                         docs_length=n_docs)
            docs_bytes_length = calcsize(docs_fmt)
            index[word] = list(unpack(docs_fmt, bytes[start_pos:start_pos + docs_bytes_length]))
            start_pos += docs_bytes_length
        return InvertedIndex(index)


class InvertedIndex:
    def __init__(self, index: Dict[str, List[int]], storage_policy='json'):
        self.index = index
        self.storage_policy = storage_policy.lower()

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
        if self.storage_policy == 'json':
            JSONStoragePolicy.dump(self.index, filepath)
        elif self.storage_policy == 'struct':
            StructStoragePolicy.dump(self.index, filepath)
        else:
            raise ValueError(f'Unknown storage policy: {self.storage_policy}')

    @classmethod
    def load(cls, filepath: str, storage_policy) -> InvertedIndex:
        """Load Inverted Index from filepath"""
        storage_policy = storage_policy.lower()
        if storage_policy == 'json':
            return JSONStoragePolicy.load(filepath)
        elif storage_policy == 'struct':
            return StructStoragePolicy.load(filepath)
        else:
            raise ValueError(f'Unknown storage policy: {storage_policy}')


def load_documents(filepath: str) -> Dict[int, str]:
    documents = {}
    with open(filepath) as fio:
        lines = fio.readlines()
        for line in lines:
            doc_id, content = line.lower().split("\t", 1)
            documents[int(doc_id)] = content.strip()
    return documents


def build_inverted_index(documents: Dict[int, str], storage_policy='json') -> InvertedIndex:
    index = defaultdict(list)
    for key, content in documents.items():
        words = re.split(r"\W+", content)
        for word in set(words):
            if word not in index or key not in index[word]:
                index[word].append(key)
    return InvertedIndex(index, storage_policy)


def callback_build(arguments):
    documents = load_documents(arguments.dataset)
    inverted_index = build_inverted_index(documents, storage_policy=arguments.strategy)
    inverted_index.dump(arguments.output)


def callback_query(arguments):
    inverted_index = InvertedIndex.load(filepath=arguments.index,
                                        storage_policy=arguments.strategy)
    if arguments.query is not None:
        process_query_from_cli(arguments.query, inverted_index)
    elif hasattr(arguments, 'query_file'):
        process_query_from_file(arguments.query_file, inverted_index)


def process_query_from_cli(queries, inverted_index):
    for words in queries:
        res = make_result_of_query_in_one_line(inverted_index.query(words))
        print(res, file=sys.stdout)


def process_query_from_file(query_file, inverted_index):
    for query in query_file:
        query = re.split(r"\W+", query.strip())
        res = make_result_of_query_in_one_line(inverted_index.query(query))
        print(res, file=sys.stdout)


def make_result_of_query_in_one_line(arr: List):
    return ','.join([str(el) for el in arr])


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
    parser_build.add_argument('-s', '--strategy', default='struct', choices=['json', 'struct'])
    parser_build.set_defaults(callback=callback_build)

    parser_query = subparsers.add_parser('query', help='Query inverted index with words',
                                         formatter_class=ArgumentDefaultsHelpFormatter)
    parser_query.add_argument('--index', required=True, help='Path to inverted index')
    parser_query.add_argument('-s', '--strategy', default='struct', choices=['json', 'struct'])

    query_group = parser_query.add_mutually_exclusive_group(required=True)
    query_group.add_argument('--query', nargs='+', action='append', metavar='WORD',
                             help='Query with words from CLI')
    query_group.add_argument('--query-file-utf8', dest='query_file',
                             type=EncodedFileType('r', encoding='utf-8'),
                             default=TextIOWrapper(sys.stdin.buffer, encoding='utf-8'),
                             help='Load queries from file with utf-8 encoding')
    query_group.add_argument('--query-file-cp1251', dest='query_file',
                             type=EncodedFileType('r', encoding='cp1251'),
                             default=TextIOWrapper(sys.stdin.buffer, encoding='cp1251'),
                             help='Load queries from file with cp-1251 encoding')

    parser_query.set_defaults(callback=callback_query)


def main():
    parser = ArgumentParser(prog='Inverted Index CLI',
                            description='Lib to build, load, dump and query Inverted Index')
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()
