#!/usr/bin/env python3

import os
import re
from datetime import datetime
from functools import reduce

import click
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
    with open(pom) as fin:
        modules = BeautifulSoup(fin, 'xml').select('project modules module')
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


def remove_dependency_if_possible(pom, dependency, mvn_cmd):
    place_holder = '<!-- TEST -->\n'
    replace(pom, dependency, place_holder)

    work_path = os.path.split(pom)[0]
    cmd = f'cd {work_path} && {mvn_cmd} &> /dev/null'
    if os.system(cmd):
        replace(pom, place_holder, dependency)
        return False
    else:
        replace(pom, place_holder, '\n')
        return True


@click.command()
@click.option('--pom', prompt=True, type=str, help='/path/to/pom.xml')
@click.option('--mvn_cmd', prompt=True, default='mvn clean install -DskipTest=True', type=str,
              help='the maven command for build project or module', show_default=True)
@click.option('--project/--module', default=True,
              help='execute maven command for project or module? default for project')
def main(pom, mvn_cmd, project):
    '''
    This script will remove extra Maven dependencies of
    special project and all it's sub modules.

    Dependencies are removed one by one and
    if the maven command is successful the dependency is left out.

    The default maven command is `mvn clean install -DskipTests=true`
    '''
    begin_time = datetime.now()
    poms_and_dependencies = get_poms_and_dependencies(pom)
    all_dependencies = reduce((lambda a, b: a + b), poms_and_dependencies.values())
    print(f'Total number of pom.xml files {len(poms_and_dependencies)}, '
          f'total number of dependencies {len(all_dependencies)}')

    counter = 1
    deleted = 0
    for module_pom, dependencies in poms_and_dependencies.items():
        print(f'Handling {len(dependencies)} dependencies of {module_pom}')
        for dependency in dependencies:
            group_id = re.match('[\s\S]*<groupId>(.*)</groupId>', dependency).group(1)
            artifact_id = re.match('[\s\S]*<artifactId>(.*)</artifactId>', dependency).group(1)

            deleted_str = click.style(f'deleted: {deleted}', bold=True, fg='green')
            click.secho(f'{counter}/{len(all_dependencies)}({deleted_str}): remove {group_id}:{artifact_id}...', nl=False)

            if remove_dependency_if_possible(pom if project else module_pom, dependency, mvn_cmd):
                click.secho('SUCCESS', bold=True, blink=True, fg='green')
                deleted += 1
            else:
                click.secho('FAILED', bold=True)
            counter += 1
    elapsed = datetime.now() - begin_time
    click.secho(f'Total remove {deleted} dependencies, elapsed time: {elapsed}', bold=True, blink=True, fg='green')


if '__main__' == __name__:
    main()
