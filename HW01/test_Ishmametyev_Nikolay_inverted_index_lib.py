import task_Ishmametyev_Nikolay_inverted_index_lib as lib


def test_load_documents_return_dict():
    """Check type of loaded documents"""
    loaded_documents = lib.load_documents('text.txt')
    assert isinstance(loaded_documents, dict)


def test_load_documents_default_docs():
    """Test loading of default documents"""
    expected_documents = {1: 'this doc consists one word',
                          2: 'this doc consists two words',
                          3: 'this doc also consists two words'}
    loaded_documents = lib.load_documents('text.txt')
    assert expected_documents == loaded_documents


def test_build_inverted_index():
    """Test index building with default docs"""
    expected_dict = {'this': [1, 2, 3], 'doc': [1, 2, 3], 'word': [1],
                     'consists': [1, 2, 3], 'two': [2, 3], 'one': [1],
                     'words': [2, 3], 'also': [3]}
    expected_index = lib.InvertedIndex(expected_dict)
    documents = lib.load_documents('text.txt')
    index = lib.build_inverted_index(documents)
    assert expected_index == index


def test_index_dump_and_load():
    """Test file operation of InvertedIndex"""
    filepath = 'inverted.index'
    documents = lib.load_documents('text.txt')
    index = lib.build_inverted_index(documents)
    index.dump(filepath)
    loaded_index = lib.InvertedIndex.load(filepath)
    assert loaded_index == index


def test_index_query_with_existed_words():
    """Test query with words that index consists"""
    expected_answer = [2, 3]
    documents = lib.load_documents('text.txt')
    index = lib.build_inverted_index(documents)
    query = ["two", "words"]
    answer = index.query(query)
    assert expected_answer == answer


def test_index_query_with_non_existed_words():
    """Test query with words that index does not consist"""
    expected_answer = []
    documents = lib.load_documents('text.txt')
    index = lib.build_inverted_index(documents)
    query = ["made"]
    answer = index.query(query)
    assert expected_answer == answer
