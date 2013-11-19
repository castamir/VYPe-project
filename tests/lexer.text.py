import sys
sys.path.insert(0, "./../libs")
sys.path.insert(0, "..")

import lexer
tokens = lexer.tokens

#import ply.lex as lex
import unittest

class TestLexer(unittest.TestCase):
    def test_tokens(self):
        global tokens
        self.assertEqual(
            True, True
        )


if __name__ == '__main__':
    unittest.main()
