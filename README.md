# Maven Dependencies Optimizer

## 背景

随着时间推移, Java 项目会加入越来越多的依赖项, 并且部分依赖会因业务或解决方案的变迁而弃用. 如果一直放任不管, 可能会产生以下问题:

1.  产生无谓的依赖冲突;
2.  编译打包时间长, 输出包文件较大;
3.  IDE 加载耗时...;
4.  处女座无法忍受;

然而目前市面上只有 maven-dependency-plugin 提供分析多余依赖的解决方案, 并且它是根据编译后的字节码分析依赖关系的, 而这时已经丢失了:

1. 没有定义任何类但提供传递依赖的依赖项, 这在 Spring Boot 中经常出现, 如 **spring-boot-starter-test** 就只写了一堆依赖, 如 **spring-boot-test**, **junit**, **mockito** 等, 自身没有任何代码;
2. 通过反射使用的依赖项, 这也经常在 Spring Boot 项目中出现, 各种 autoconfigure 就通过它确定运行时依赖项/解决方案;
3. 只定义了常量的依赖项, 这个公司项目中遇到过. 在编译时会发生变量替换, 对字节码和运行时 classpath 来说, 已经不需要它们了;
4. 只定义了注解的依赖项, 在编译时也会被优化掉(TODO: 验证);

所以用 `mvn dependency:analyze` 一分析, 好多依赖项是 **Unused declared dependencies**, 删掉它们后项目肯定无法启动了...但是依次测试和删除每个依赖项的时间成本太高了, 不具备可操作性. 

开始打算自己写个依赖分析和优化的工具, 但想到需要分析项目代码, 解析所有依赖项及其传递依赖与项目代码的关系, 其实复杂度还是挺高的. 

## 解决方案

想想 Java 霸占编程语言排行榜多年, 肯定有人产生同样的困扰, 所以就在网上搜啊搜, 结果找到这个项目: [maven-cleanup](https://github.com/siivonen/maven-cleanup). 这位同学在 12 年 1 月份实现了一个看起来比较笨, 但行之有效的解决方案: **自动化测试验证每一个依赖项被删除后项目是否还能正确编译打包**, 如果可以, 那说明该依赖项是多余的, 可以删除; 否则保留它.

其实, 多余依赖分两种情况:
1. 整个项目都不再使用的依赖项, 是需要彻底删除的;
2. 模块间依赖错位. 比说 A 模块依赖 B 模块, B 模块不依赖 fastjson, 但有 fastjson 依赖项. A 模块通过 B 模块传递依赖 fastjson. 这种情况下不能删除 fastjson, 而是调整其所在的模块.

[maven-cleanup](https://github.com/siivonen/maven-cleanup) 因为处理方式的问题, 对上述两种情况支持不太好, 事后手工维护成本挺高的, 所以就用 python 重写了一遍, 并增加了些功能:

1.  支持分析和去除整个项目都不再使用的依赖项;
2.  支持分析和去除单个模块不再使用的依赖项;
3.  增加统计信息;

在 **分析和去除单个模块不再使用的依赖项** 时, 因为存在传递依赖的可能性, 所以可能会出现这种情况: **删除一个依赖项后导致后续其他模块都编译出错(缺少传递依赖)**. 所以每次完成优化后要手动编译下整个项目, 确认是否存在受影响的模块, 并在受影响的模块添加缺少的依赖项.

## 使用方法

```sh
$ git clone https://github.com/cnfn/maven_dependencies_optimizer.git
$ cd maven_dependencies_optimizer
$ pip install -r requirements.txt
$ ./remove_extra_dependencies.py --help
Usage: remove_extra_dependencies.py [OPTIONS]

  This script will remove extra Maven dependencies of special project and
  all it's sub modules.

  Dependencies are removed one by one and if the maven command is successful
  the dependency is left out.

  The default maven command is `mvn clean install -DskipTests=true`

Options:
  --pom TEXT            /path/to/pom.xml
  --mvn_cmd TEXT        the maven command for build project or module
                        [default: mvn clean install -DskipTest=True]
  --project / --module  execute maven command for project or module? default
                        for project
  --help                Show this message and exit.

$ ./remove_extra_dependencies.py --pom /path/to/pom.xml --mvn_cmd 'mvn clean install'
Total number of pom.xml files 1, total number of dependencies 8
Handling 8 dependencies of /path/to/pom.xml
1/8(deleted: 0): remove org.springframework.boot:spring-boot-starter-jooq...FAILED
2/8(deleted: 0): remove org.jooq:jooq-meta...SUCCESS
3/8(deleted: 1): remove org.jooq:jooq-codegen...FAILED
4/8(deleted: 1): remove com.h2database:h2...SUCCESS
5/8(deleted: 2): remove org.springframework.boot:spring-boot-starter-test...FAILED
6/8(deleted: 2): remove org.projectlombok:lombok...SUCCESS
7/8(deleted: 3): remove com.alibaba:fastjson...SUCCESS
8/8(deleted: 4): remove org.assertj:assertj-core...SUCCESS
Total remove 5 dependencies, elapsed time: 0:00:50.119186
```