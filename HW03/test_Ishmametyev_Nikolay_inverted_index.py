import os
import pytest
from textwrap import dedent
from argparse import Namespace

import task_Ishmametyev_Nikolay_inverted_index as lib

DOCUMENTS_EXAMPLE = dedent("""\
    1	This doc consists one слово
    2	This doc consists two words
    3	This doc also consists two words
    """)

DOCUMENTS_DICT_EXAMPLE = {
    1: 'this doc consists one слово',
    2: 'this doc consists two words',
    3: 'this doc also consists two words'
}

INVERTED_INDEX_EXAMPLE = {
    'this': [1, 2, 3], 'doc': [1, 2, 3], 'слово': [1],
    'consists': [1, 2, 3], 'two': [2, 3], 'one': [1],
    'words': [2, 3], 'also': [3]
}

DATASET_FILE_PATH_TINY = 'text.txt'
DATASET_FILE_PATH_BIG = 'wikipedia_sample.txt'


@pytest.fixture()
def example_dataset_io(tmpdir):
    dataset_fio = tmpdir.join(DATASET_FILE_PATH_TINY)
    dataset_fio.write(DOCUMENTS_EXAMPLE)
    return dataset_fio


@pytest.fixture()
def create_json_index_from_documents(example_dataset_io):
    documents = lib.load_documents(example_dataset_io)
    index = lib.build_inverted_index(documents, storage_policy='json')
    return index


@pytest.fixture()
def create_struct_index_from_documents(example_dataset_io):
    documents = lib.load_documents(example_dataset_io)
    index = lib.build_inverted_index(documents, storage_policy='struct')
    return index


def test_load_documents_return_dict(example_dataset_io):
    """Check type of loaded documents"""
    loaded_documents = lib.load_documents(example_dataset_io)
    assert isinstance(loaded_documents, dict)


def test_load_documents_default_docs(example_dataset_io):
    """Test loading of default documents"""
    loaded_documents = lib.load_documents(example_dataset_io)
    assert DOCUMENTS_DICT_EXAMPLE == loaded_documents


def test_build_inverted_index(example_dataset_io):
    """Test index building with default docs"""
    expected_index = lib.InvertedIndex(INVERTED_INDEX_EXAMPLE)
    documents = lib.load_documents(example_dataset_io)
    index = lib.build_inverted_index(documents, storage_policy='json')
    assert expected_index == index

    index = lib.build_inverted_index(documents, storage_policy='struct')
    assert expected_index == index


def test_index_dump_json_and_load(tmpdir, create_json_index_from_documents):
    """Test file operation of InvertedIndex"""
    filepath = tmpdir.join('inverted.index')
    index = create_json_index_from_documents
    index.dump(filepath)
    loaded_index = lib.InvertedIndex.load(filepath, storage_policy='json')
    assert loaded_index == index


def test_index_dump_struct_and_load(tmpdir, create_struct_index_from_documents):
    """Test file operation of InvertedIndex"""
    filepath = tmpdir.join('inverted.index')
    index = create_struct_index_from_documents
    index.dump(filepath)
    loaded_index = lib.InvertedIndex.load(filepath, storage_policy='struct')
    assert loaded_index == index


def test_index_query_with_empty_query(create_json_index_from_documents):
    """Test query with words that index consists"""
    expected_answer = []
    query = []
    index = create_json_index_from_documents
    answer = index.query(query)
    assert expected_answer == answer


def test_index_query_with_existed_words(create_json_index_from_documents):
    """Test query with words that index consists"""
    expected_answer = [2, 3]
    index = create_json_index_from_documents
    query = ["two", "words"]
    answer = index.query(query)
    assert expected_answer == answer


def test_index_query_with_non_existed_words(create_json_index_from_documents):
    """Test query with words that index does not consist"""
    expected_answer = []
    index = create_json_index_from_documents
    query = ["made"]
    answer = index.query(query)
    assert expected_answer == answer


def test_process_query(tmpdir, create_json_index_from_documents, capsys):
    storage_policy = 'json'
    words = ['two', 'words']
    filepath = os.path.join(tmpdir.dirname, 'inverted.index')
    index = create_json_index_from_documents
    index.dump(filepath)
    expected_res = lib.make_result_of_query_in_one_line(index.query(words))

    arguments = Namespace(index=filepath, query=[words], strategy=storage_policy)
    lib.callback_query(arguments)
    captures = capsys.readouterr()
    assert expected_res in captures.out
