# Maven Dependencies Optimizer

随着时间推移, 项目会加入越来越多的依赖项, 并且部分依赖会因业务或解决方案的变迁而弃用.
目前市面上只有 maven-dependency-plugin 提供解决方案, 但它是根据编译后的字节码分析依赖关系的, 而这时已经丢失了:
1. 没有定义任何类但提供传递依赖的依赖项, 这在 Spring Boot 中经常出现, 如 **spring-boot-starter-test** 就只写了一堆依赖, 如 **spring-boot-test**, **junit**, **mockito** 等, 自身没有任何代码;
2. 通过反射使用的依赖项, 这也经常在 Spring Boot 项目中出现, 各种 autoconfigure 就通过它确定运行时依赖项/解决方案;
3. 只定义了常量的依赖项, 这个公司项目中遇到过. 在编译时会发生变量替换, 对字节码和运行时 classpath 来说, 已经不需要它们了;
4. 只定义了注解的依赖项, 在编译时也会被优化掉(TODO: 验证);

所以用 `mvn dependency:analyze` 一分析, 好多依赖项是 **Unused declared dependencies**, 删掉它们后项目肯定无法启动了...
依次测试和删除每个依赖项的时间成本太高了, 所以大家一般就会放任不管. 但这也有问题:
1. 可能会产生无谓的依赖冲突;
2. 编译打包时间长, 输出包文件较大;
3. IDE 加载耗时...;
4. 处女座无法忍受;

开始想自己写个依赖分析和优化的工具, 但想到需要分析项目代码, 解析所有依赖项及其传递依赖与项目代码的关系, 想想还是挺复杂的. 

想想 Java 霸占编程语言排行榜多年, 肯定有人产生同样的困扰, 所以就在网上搜啊搜, 结果找到这个项目: [maven-cleanup](https://github.com/siivonen/maven-cleanup). 这位同学在 12 年 1 月份实现了一个看起来比较笨, 但行之有效的解决方案: **自动化测试验证每一个依赖项被删除后项目是否还能正确编译打包**,
如果可以, 那说明该依赖项是多余的, 可以删除; 否则保留它.

它对单模块项目有很好的支持, 但对于多模块项目, 它还是解决每一个模块依赖, 忽略了模块间传递依赖的情况. 比说 A 模块依赖 B 模块, B 模块不依赖 fastjson, 但有 fastjson 依赖项. A 模块通过 B 模块传递依赖 fastjson. 这种情况下它只会发现 B 模块不依赖 fastjson, 于是就删除该依赖了. 然后会导致后续所有测试失败. 最终交付的也不是一个可运行的项目.

针对这个问题, 可以分两部解决:
1. 每次都编译打包和测试所有模块, 保证所有模块正常, 剔除整个项目不再需要的依赖项;
2. 针对每个模板编译打包和测试, 保证每个模块都只依赖自己必要的依赖项, 不存在模块间的传递依赖情况.

第二步可能需要运行多次才可以达到相应目标.