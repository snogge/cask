from unittest import TestCase
import os
import sys
sys.path.append('../bin')
sys.path.append('bin')

from commander import tokenizer, reader, read_from_tokens, ParseError

CASKCLI = os.path.join(os.path.dirname(__file__), '../cask-cli.el')

DEFUN = """
(defun foo ()
  "docstring" ;and a comment
  (message "text"))
"""

SAMPLE = """
(eval-and-compile
  (defconst cask-directory
    (file-name-directory
     (cond
      (load-in-progress load-file-name)
      ((and (boundp 'byte-compile-current-file) byte-compile-current-file)
       byte-compile-current-file)
      (:else (buffer-file-name))))
    "Path to Cask root."))
"""


class TestTokenizer(TestCase):
    """Test the tokenizer generator function."""

    def test_simple_defun(self):
        """Tokenize a simple defun"""
        self.assertEqual(['(', 'defun', 'foo', '(', ')', '"docstring"',
                          '(', 'message', '"text"', ')', ')'],
                         list(tokenizer(DEFUN)))

    def test_code(self):
        """tokenize some sample code from cask-cli.el"""
        self.assertEqual(['(', 'eval-and-compile',
                          '(', 'defconst', 'cask-directory',
                          '(', 'file-name-directory',
                          '(', 'cond',
                          '(', 'load-in-progress', 'load-file-name', ')',
                          '(', '(', 'and', '(', 'boundp',
                          "'", "byte-compile-current-file", ')',
                          'byte-compile-current-file', ')',
                          'byte-compile-current-file', ')',
                          '(', ':else', '(', 'buffer-file-name', ')', ')', ')',
                          ')',
                          '"Path to Cask root."', ')', ')'],
                         list(tokenizer(SAMPLE)))

    def test_quoted_list(self):
        """Tokenize a quoted list"""
        self.assertEqual(["'", '(', 'bar', 'foo', ')'],
                         list(tokenizer("'(bar foo)")))

    def test_backquoted_list(self):
        """Tokenize a backquoted list with comma-expressions"""
        self.assertEqual(['`', '(', ',', 'bar', 'foo',
                          ',', '(', 'test', 'arg', ')', ')'],
                         list(tokenizer("""`(,bar foo
                         ,(test arg))""")))

    def test_unterminated_string(self):
        """Error on unterminated string"""
        with self.assertRaises(ParseError):
            list(tokenizer("""(message "fooo"""))

    def test_tokenize_caskcli(self):
        """Tokenize cask-cli.el"""
        with open(CASKCLI) as cli:
            self.assertTrue(list(tokenizer(cli.read())))


class TestReader(TestCase):
    """Test the token reader function."""
    def test_simple_defun(self):
        """Read a simple defun"""
        expected = ['defun', 'foo', [], 'docstring',
                    ['message', 'text', ]]
        self.assertEqual(expected,
                         read_from_tokens(list(tokenizer(DEFUN))))
        self.assertEqual(expected,
                         reader(tokenizer(DEFUN)))
        self.assertEqual(expected,
                         reader(list(tokenizer(DEFUN))))

    def test_code(self):
        """Read some sample code from cask-cli.el"""
        expected = ['eval-and-compile',
                    ['defconst', 'cask-directory',
                     ['file-name-directory',
                      ['cond',
                       ['load-in-progress', 'load-file-name'],
                       [['and', ['boundp', "'", 'byte-compile-current-file'],
                         'byte-compile-current-file'],
                        'byte-compile-current-file'],
                       [':else', ['buffer-file-name']]]],
                     "Path to Cask root."]]
        self.assertEqual(expected,
                         read_from_tokens(list(tokenizer(SAMPLE))))
        self.assertEqual(expected, reader(tokenizer(SAMPLE)))
        self.assertEqual(expected, reader(list(tokenizer(SAMPLE))))

    def test_quoted_list(self):
        """Read a quoted list"""
        code = "'(bar foo)"
        expected = ["'", ['bar', 'foo']]
        tokens = list(tokenizer(code))
        self.assertEqual(expected[0], read_from_tokens(tokens))
        self.assertEqual(expected[1], read_from_tokens(tokens))
        tokengen = tokenizer(code)
        self.assertEqual(expected[0], reader(tokengen))
        self.assertEqual(expected[1], reader(tokengen))
        # So this shows a weakness in the reader function, it keeps
        # its state in the input iterator. So when the input is not an
        # iterator, it cannot keep state...
        tokens = list(tokenizer(code))
        self.assertEqual(expected[0], reader(tokens))
        self.assertEqual(expected[1], reader(tokens[1:]))

    def test_backquoted_list(self):
        """Read a backquoted list with comma-expressions"""
        code = """`(,bar foo ,(test arg))"""
        expected = ['`', [',', 'bar', 'foo', ',', ['test', 'arg']]]
        tokens = list(tokenizer(code))
        self.assertEqual(expected[0], read_from_tokens(tokens))
        self.assertEqual(expected[1], read_from_tokens(tokens))
        tokengen = tokenizer(code)
        self.assertEqual(expected[0], reader(tokengen))
        self.assertEqual(expected[1], reader(tokengen))
        # So this shows a weakness in the reader function, it keeps
        # its state in the input iterator. So when the input is not an
        # iterator, it cannot keep state...
        tokens = list(tokenizer(code))
        self.assertEqual(expected[0], reader(tokens))
        self.assertEqual(expected[1], reader(tokens[1:]))

    def test_unexpected_eof(self):
        """Error on unexpected EOF."""
        code = """(defun foo ("""
        with self.assertRaises(ParseError):
            read_from_tokens(list(tokenizer(code)))
        with self.assertRaises(ParseError):
            reader(tokenizer(code))
        with self.assertRaises(ParseError):
            reader(list(tokenizer(code)))

    def test_unexpected_closing_paren(self):
        """Error on unexpected ("""
        code = """)"""
        with self.assertRaises(ParseError):
            read_from_tokens(list(tokenizer(code)))
        with self.assertRaises(ParseError):
            reader(tokenizer(code))
        with self.assertRaises(ParseError):
            reader(list(tokenizer(code)))

    def test_reading_caskcli(self):
        """Read cask-cli.el"""
        with open(CASKCLI) as cli:
            tokens = list(tokenizer(cli.read()))
            while tokens:
                self.assertTrue(read_from_tokens(tokens))
        with open(CASKCLI) as cli:
            tokens = tokenizer(cli.read())
            sexp = reader(tokens)
            while sexp is not None:
                sexp = reader(tokens)
        ## Can't think of any easy way to make this work...
        # with open(CASKCLI) as cli:
        #     tokens = list(tokenizer(cli.read()))
        #     sexp = reader(tokens)
        #     while sexp is not None:
        #         sexp = reader(tokens)
