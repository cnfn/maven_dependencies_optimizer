#!/usr/bin/env python3

import os
import shutil
import tempfile
import unittest

from remove_extra_dependencies import get_dependencies
from remove_extra_dependencies import get_modules
from remove_extra_dependencies import get_poms_and_dependencies
from remove_extra_dependencies import replace


class TestRemoveExtraDependencies(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_pom = os.path.join(self.tmp_dir, 'pom.xml')

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def _generate_pom_file_have_modules(self):
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://maven.apache.org/POM/4.0.0"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modules>
        <module>module-a</module>
        <module>module-b</module>
    </modules>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-jooq</artifactId>
        </dependency>
        <dependency>
            <groupId>org.jooq</groupId>
            <artifactId>jooq-codegen</artifactId>
        </dependency>
    </dependencies>
</project>
        '''
        with open(self.tmp_pom, 'w') as fout:
            fout.write(content)

    def _generate_pom_file_no_modules(self):
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://maven.apache.org/POM/4.0.0"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-jooq</artifactId>
        </dependency>
        <dependency>
            <groupId>org.jooq</groupId>
            <artifactId>jooq-codegen</artifactId>
        </dependency>
    </dependencies>
</project>
        '''
        with open(self.tmp_pom, 'w') as fout:
            fout.write(content)

    def test_get_dependencies(self):
        self._generate_pom_file_have_modules()

        dependencies = get_dependencies(self.tmp_pom)
        self.assertEqual(2, len(dependencies))
        self.assertIn('spring-boot', dependencies[0])
        self.assertIn('org.jooq', dependencies[1])

    def test_get_modules(self ):
        self._generate_pom_file_have_modules()

        modules = get_modules(self.tmp_pom)
        self.assertEqual(2, len(modules))
        self.assertIn('module-a', modules)
        self.assertIn('module-b', modules)

    def test_get_poms_and_dependencies(self):
        self._generate_pom_file_no_modules()

        result = get_poms_and_dependencies(self.tmp_pom)
        self.assertIn(self.tmp_pom, result)
        self.assertEqual(2, len(result[self.tmp_pom]))

    def test_replace(self):
        self._generate_pom_file_have_modules()

        old_str = 'org.jooq'
        new_str = 'begin\nCONTENT\nend'
        replace(self.tmp_pom, old_str, new_str)

        with open(self.tmp_pom) as fin:
            content = fin.read()
            self.assertIn(new_str, content)


if '__main__' == __name__:
    unittest.main()
