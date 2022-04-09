# boke

> 这是一个有两段的块引用。这是第一段。
>
> 这是第二段。Vestibulum enim wisi, viverra nec, fringilla in, laoreet vitae, risus.

> 这是另一个只有一个段落的块引用。有三个空行分隔两个块引用。

## 无序列表

*   红色
*   绿色
*   蓝色

## 有序列表

1.  红色
2. 	绿色
3.	蓝色

- [ ] 这是一个任务列表项
- [ ] 需要在前面使用列表的语法
- [ ] normal **formatting**, @mentions, #1234 refs
- [ ] 未完成
- [x] 完成

```
function test() {
  console.log("notice the blank line before this function?");
}
```

语法高亮：
```ruby
require 'redcarpet'
markdown = Redcarpet.new("Hello World!")
puts markdown.to_html
```

$$
\mathbf{V}_1 \times \mathbf{V}_2 =  \begin{vmatrix} 
\mathbf{i} & \mathbf{j} & \mathbf{k} \\
\frac{\partial X}{\partial u} &  \frac{\partial Y}{\partial u} & 0 \\
\frac{\partial X}{\partial v} &  \frac{\partial Y}{\partial v} & 0 \\
\end{vmatrix}
$$

| First Header  | Second Header |
| ------------- | ------------- |
| Content Cell  | Content Cell  |
| Content Cell  | Content Cell  |


| Left-Aligned  | Center Aligned  | Right Aligned |
| :------------ |:---------------:| -----:|
| col 3 is      | some wordy text | $1600 |
| col 2 is      | centered        |   $12 |
| zebra stripes | are neat        |    $1 |

------

您可以像这样创建脚注[^footnote].

[^footnote]: Here is the *text* of the **footnote**.

<https://typlog.com/>

******


This is [an example](http://example.com/ "Title") inline link.

[This link](http://example.net/) has no title attribute.

This is [an example][id] reference-style link.

然后，在文档中的任何位置，您可以单独定义链接标签，如下所示：

[id]: http://example.com/  "Optional Title Here"

[Google][]
然后定义链接：

[Google]: http://google.com/

*单个星号*

_单个下划线_


    wow_great_stuff

    do_this_and_do_that_and_another_thing.

\*这个文字被文字星号包围\*


**双星号**

__双重下划线__

**双星号 _单个下划线_ **

**双星号 `printf()` **

使用`printf()`函数。

~~错误的文字。~~ 

<u>下划线</u> 

例如： $\lim_{x \to \infty} \exp(-x) = 0$ 将呈现为LaTeX命令。



