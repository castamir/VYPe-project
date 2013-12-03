#!/usr/bin/env python
# -*- coding: utf-8 -*-
import getopt
import sys
from Parser import parse, SyntaxErrorException
from Semantic import SemanticErrorException
from Scanner import LexicalErrorException


class RuntimeException(Exception):
    pass


class VYPeProject:
    def __init__(self):
        self.input_file = None
        self.help = False

    @staticmethod
    def print_help():
        print "VYPe project 2013 help..."

    def parse_args(self):
        try:
            opt, args = getopt.getopt(sys.argv[1:], "h", ["help", "file="])
        except getopt.GetoptError as e:
            raise RuntimeException("Unknown argument '%s'" % e.args[1])
        for o, a in opt:
            if o in ['--help', '-h']:
                self.help = True
            elif o == '--file':
                self.input_file = a

    def run(self):
        self.parse_args()
        if self.help:
            self.print_help()
            return 0
        if self.input_file is None:
            raise RuntimeException("Missing input file. Try it again with -h to see more.")
        with open(self.input_file, "r") as my_file:
            data = my_file.read()
        tac = self.parse(data)
        self.generate_target_program(tac)
        return 0

    @staticmethod
    def parse(data):
        tac = parse(data)
        # debug prints
        if tac is not None:
            for line in tac:
                print line
                pass
        return tac

    def generate_target_program(self, tac):
        pass


if __name__ == "__main__":
    project = VYPeProject()
    try:
        exitcode = project.run()
    except LexicalErrorException as e:
        print >> sys.stderr, "Line %d: %s" % (e.line, e.message)
        exitcode = 1
    except SyntaxErrorException as e:
        print >> sys.stderr, "Line %d: %s" % (e.line, e.message)
        exitcode = 2
    except SemanticErrorException as e:
        print >> sys.stderr, "Line %d: %s" % (e.line, e.message)
        exitcode = 3
    except RuntimeException as e:
        print >> sys.stderr, e.message
        exitcode = 5
    except Exception as e:
        print >> sys.stderr, "Runtime error occurred.", e.message
        exitcode = 5
    sys.exit(exitcode)
