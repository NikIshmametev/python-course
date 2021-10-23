import pytest
from textwrap import dedent

import task_Ishmametyev_Nikolay_inverted_index_lib as lib

DOCUMENTS_EXAMPLE = dedent("""\
    1	This doc consists one word
    2	This doc consists two words
    3	This doc also consists two words
    """)

DOCUMENTS_DICT_EXAMPLE = {
    1: 'this doc consists one word',
    2: 'this doc consists two words',
    3: 'this doc also consists two words'
}

INVERTED_INDEX_EXAMPLE = {
    'this': [1, 2, 3], 'doc': [1, 2, 3], 'word': [1],
    'consists': [1, 2, 3], 'two': [2, 3], 'one': [1],
    'words': [2, 3], 'also': [3]
}


@pytest.fixture()
def example_dataset_io(tmpdir):
    dataset_fio = tmpdir.join('text.txt')
    dataset_fio.write(DOCUMENTS_EXAMPLE)
    return dataset_fio


def test_load_documents_return_dict(example_dataset_io):
    """Check type of loaded documents"""
    loaded_documents = lib.load_documents(example_dataset_io)
    assert isinstance(loaded_documents, dict)


def test_load_documents_default_docs(tmpdir, example_dataset_io):
    """Test loading of default documents"""
    loaded_documents = lib.load_documents(example_dataset_io)
    assert DOCUMENTS_DICT_EXAMPLE == loaded_documents


def test_build_inverted_index(example_dataset_io):
    """Test index building with default docs"""
    expected_index = lib.InvertedIndex(INVERTED_INDEX_EXAMPLE)
    documents = lib.load_documents(example_dataset_io)
    index = lib.build_inverted_index(documents)
    assert expected_index == index


def test_index_dump_and_load(tmpdir, example_dataset_io):
    """Test file operation of InvertedIndex"""
    filepath = tmpdir.join('inverted.index')
    documents = lib.load_documents(example_dataset_io)
    index = lib.build_inverted_index(documents)
    index.dump(filepath)
    loaded_index = lib.InvertedIndex.load(filepath)
    assert loaded_index == index


def test_index_query_with_existed_words(example_dataset_io):
    """Test query with words that index consists"""
    expected_answer = [2, 3]
    documents = lib.load_documents(example_dataset_io)
    index = lib.build_inverted_index(documents)
    query = ["two", "words"]
    answer = index.query(query)
    assert expected_answer == answer


def test_index_query_with_non_existed_words(example_dataset_io):
    """Test query with words that index does not consist"""
    expected_answer = []
    documents = lib.load_documents(example_dataset_io)
    index = lib.build_inverted_index(documents)
    query = ["made"]
    answer = index.query(query)
    assert expected_answer == answer
