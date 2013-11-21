import sys
sys.path.insert(0, "./../libs")
sys.path.insert(0, "..")

import ply.lex as lex
import lexer
tokens = lexer.tokens

#import ply.lex as lex
import unittest

class TestLexer(unittest.TestCase):
    def setUp(self):
        self.lex = lex

    def test_tokens(self):
        self.lex.input("identifikator if 5 \"nejaky retezec\"")
        tokens = []
        while True:
            tok = self.lex.token()
            if not tok: break
            tokens.append(tok.type)
        self.assertEqual(
            tokens,
            ['ID', 'IF', 'CINT', 'CSTRING']
        )

    #def test_illegal(self):
    #    self.lex.input('ahoj ~ ahoj')
    #    allCorrect = True
    #    while True:
    #        tok = self.lex.token()
    #        if not tok:
    #            allCorrect = False
    #            break
    #    self.assertEqual(
    #        allCorrect,
    #        False
    #    )

    def test_fibo_loop(self):
        with open ("examples/fibo.loop.src", "r") as myfile:
            data=myfile.read()
            tokens = []
            self.lex.input(data)
            while True:
                tok = self.lex.token()
                if not tok: break
                tokens.append(tok.type)
        self.assertEqual(
            tokens,
            ['INT', 'ID', 'LPAREN', 'VOID', 'RPAREN', 'LBRACE', 'INT', 'ID', 'COMMA', 'ID', 'SEMI', 'ID', 'LPAREN', 'CSTRING', 'RPAREN', 'SEMI', 'ID', 'EQUALS', 'ID', 'LPAREN', 'RPAREN', 'SEMI', 'IF', 'LPAREN', 'ID', 'LT', 'CINT', 'RPAREN', 'LBRACE', 'ID', 'LPAREN', 'CSTRING', 'RPAREN', 'SEMI', 'RBRACE', 'ELSE', 'LBRACE', 'ID', 'EQUALS', 'CINT', 'SEMI', 'WHILE', 'LPAREN', 'ID', 'GT', 'CINT', 'RPAREN', 'LBRACE', 'ID', 'EQUALS', 'ID', 'TIMES', 'ID', 'SEMI', 'ID', 'EQUALS', 'ID', 'MINUS', 'CINT', 'SEMI', 'RBRACE', 'ID', 'LPAREN', 'CSTRING', 'COMMA', 'ID', 'COMMA', 'CSTRING', 'RPAREN', 'SEMI', 'RBRACE', 'RBRACE']
        )

if __name__ == '__main__':
    unittest.main()
