#!/usr/bin/env python3

import json

from remove_extra_dependencies import get_dependencies
from remove_extra_dependencies import get_modules
from remove_extra_dependencies import get_poms_and_dependencies
from remove_extra_dependencies import replace


def test_get_dependencies(pom):
  dependencies = get_dependencies(pom)
  print(dependencies)
  [print(item) for item in dependencies]

def test_get_modules(pom):
  modules = get_modules(pom)
  print(modules)


def test_get_poms_and_dependencies(pom):
  result = get_poms_and_dependencies(pom)
  print(result)
  print(json.dumps(result))

def test_replace():
  filepath = '/tmp/pom_test'
  content = '123\nCONTENT\n123'
  with open(filepath, 'w') as fout:
    fout.write(content)

  replace(filepath, 'CONTENT', 'NEW_VALUE')


if '__main__' == __name__:
  pom = '/home/cc/code/secaware-asrc/web/pom.xml'
  test_get_dependencies(pom)

  # pom = '/home/cc/code/secaware-asrc/pom.xml'
  # test_get_modules(pom)
  # test_get_poms_and_dependencies(pom)
  #
  # test_replace()
