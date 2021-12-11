from task_Ishmametyev_Nikolay_indenter import Indenter

MESSAGES = ["hi", "hello", "bonjour", "hey"]


def test_indent_with_str(capsys):
    indent_str = "--"
    indent_level = 0

    with Indenter(indent_str=indent_str, indent_level=indent_level) as indent:
        indent.print(MESSAGES[0])
        with indent:
            indent.print(MESSAGES[1])
            with indent:
                indent.print(MESSAGES[2])
        indent.print(MESSAGES[3])

    expected_output = "\n".join([
        indent_str * indent_level + MESSAGES[0],
        indent_str * (indent_level + 1) + MESSAGES[1],
        indent_str * (indent_level + 2) + MESSAGES[2],
        indent_str * indent_level + MESSAGES[3] + "\n"
    ])

    captures = capsys.readouterr()
    assert expected_output == captures.out


def test_indent_with_str_level(capsys):
    indent_str = "--"
    indent_level = 1

    with Indenter(indent_str=indent_str, indent_level=indent_level) as indent:
        indent.print(MESSAGES[0])
        with indent:
            indent.print(MESSAGES[1])
            with indent:
                indent.print(MESSAGES[2])
        indent.print(MESSAGES[3])

    expected_output = "\n".join([
        indent_str * indent_level + MESSAGES[0],
        indent_str * (indent_level + 1) + MESSAGES[1],
        indent_str * (indent_level + 2) + MESSAGES[2],
        indent_str * indent_level + MESSAGES[3] + "\n"
    ])

    captures = capsys.readouterr()
    assert expected_output == captures.out
