#!/usr/bin/env python3

import os
import re
import sys
from functools import reduce

from bs4 import BeautifulSoup
from lxml import etree


def get_dependencies(pom):
  def __lambda_element_to_str(element):
    dependency_with_namespace = etree.tostring(element).decode('UTF-8').strip(' ')
    return re.sub('<dependency.*>', '<dependency>', dependency_with_namespace)

  root = etree.parse(pom).getroot()
  dependencies = root.xpath('//ns:project/ns:dependencies/ns:dependency', namespaces={'ns': root.nsmap[None]})
  return [__lambda_element_to_str(item) for item in dependencies]


def get_modules(pom):
  modules = BeautifulSoup(open(pom), 'xml').select('project modules module')
  return [module.text for module in modules]


def get_poms_and_dependencies(pom, result={}):
  result[pom] = get_dependencies(pom)
  modules = get_modules(pom)
  for module in modules:
    sub_pom = os.path.join(os.path.split(pom)[0], module, 'pom.xml')
    get_poms_and_dependencies(sub_pom, result)

  return result


def replace(filepath, old_str, new_str):
  with open(filepath) as fin:
    content = fin.read()
    with open(filepath, 'w') as fout:
      fout.write(content.replace(old_str, new_str))


def remove_dependency_if_possible(pom, dependency):
  place_holder = '<!-- TEST -->\n'
  replace(pom, dependency, place_holder)
  cmd = 'cd {dir} && {mvn_cmd} &> /dev/null'.format(dir=os.path.split(pom)[0], mvn_cmd=sys.argv[2])
  ret = os.system(cmd)
  if ret:
    print('FAILED')
    replace(pom, place_holder, dependency)
  else:
    print('SUCCESS')
    replace(pom, place_holder, '\n')


if '__main__' == __name__:
  if 3 != len(sys.argv):
    print("Usage: {0} /path/to/root/pom.xml 'mvn command to use'".format(sys.argv[0]))
    exit(1)

  print("This script will remove extra Maven dependencies of {0} and all it's sub modules".format(sys.argv[1]))
  print("Dependencies are removed one by one and if the command '{0}' is successful the dependency is left out".format(
    sys.argv[2]))

  poms_and_dependencies = {}
  get_poms_and_dependencies(sys.argv[1], poms_and_dependencies)
  all_dependencies = reduce((lambda a, b: a + b), poms_and_dependencies.values(), [])
  print('Total number of pom.xml files {pom_count}, total number of dependencies {dependency_count}'.format(
    pom_count=len(poms_and_dependencies), dependency_count=len(all_dependencies)))

  counter = 1
  for pom, dependencies in poms_and_dependencies.items():
    print('Handling {count} dependencies of {pom}'.format(count=len(dependencies), pom=pom))
    for dependency in dependencies:
      group_id = re.match('[\s\S]*<groupId>(.*)</groupId>', dependency).group(1)
      artifact_id = re.match('[\s\S]*<artifactId>(.*)</artifactId>', dependency).group(1)
      print("{counter}/{total_count}: remove {group_id}:{artifact_id}...".format(
        counter=counter, total_count=len(all_dependencies), group_id=group_id, artifact_id=artifact_id), end='', flush=True)
      remove_dependency_if_possible(pom, dependency)
      counter += 1
