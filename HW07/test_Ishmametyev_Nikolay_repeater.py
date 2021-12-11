from task_Ishmametyev_Nikolay_repeater import (
    repeater, verbose, verbose_context,
    TEXT_BEFORE_FUNC, TEXT_BEFORE_FUNC_IN_CLASS,
    TEXT_AFTER_FUNC, TEXT_AFTER_FUNC_IN_CLASS
)


TEMPLATE_STRING = "*** Hello %s! ***"


def hello(name):
    print(TEMPLATE_STRING % name)


def test_repeater(capsys):
    count = 5
    name = "Nik"
    repeater(count)(hello)(name)

    captured = capsys.readouterr()
    expected_output = (TEMPLATE_STRING % name + "\n")*count
    assert expected_output == captured.out


def test_verbose_context(capsys):
    name = "Nik"
    verbose_context()(hello)(name)

    captured = capsys.readouterr()
    expected_output = '\n'.join([
        TEXT_BEFORE_FUNC_IN_CLASS,
        TEMPLATE_STRING % name,
        TEXT_AFTER_FUNC_IN_CLASS + "\n"
    ])
    assert expected_output == captured.out


def test_verbose(capsys):
    name = "Nik"
    verbose(hello)(name)

    captured = capsys.readouterr()
    expected_output = '\n'.join([
        TEXT_BEFORE_FUNC, TEMPLATE_STRING % name, TEXT_AFTER_FUNC + "\n"
    ])
    assert expected_output == captured.out


def test_doc_method_of_inner_func():
    expected_output = "hello"

    @verbose_context()
    def hello(name):
        return f"Hello, {name}"

    assert expected_output == hello.__name__

