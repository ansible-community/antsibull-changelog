# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Test rendering code.
"""

from __future__ import annotations

import pytest

from antsibull_changelog.config import TextFormat
from antsibull_changelog.rendering.markdown import render_as_markdown
from antsibull_changelog.rendering.utils import get_document_structure

RENDER_AS_MARKDOWN_AND_STRUCTURE_DATA = [
    (
        "empty",
        r"""""",
        "restructuredtext",
        r"""""",
        set(),
    ),
    (
        "simple-rst",
        r"""`This` *is* **a** `simple <This>`_ `test <https://example.com>`__.""",
        "restructuredtext",
        r"""<em class="title-reference">This</em> <em>is</em> <strong>a</strong> [simple](This) [test](https\://example\.com)\.""",
        set(),
    ),
    (
        "complex-rst",
        r"""
==========
Main title
==========

Some text.

.. sectnum::
.. contents:: Table of Contents

.. _label:
.. _label_2:

This is a subtitle
^^^^^^^^^^^^^^^^^^

Some test with ``code``.
Some *emphasis* and **bold** text.

A `link <https://ansible.com/)>`__.

A `reference <label>`_.

A list:

* Item 1.
* Item 2.

  This is still item 2.
* Item 3.

An enumeration:

1. Entry 1

   More of Entry 1
2. Entry 2
3. Entry 3
   Second line of entry 3

   - Sublist
   - Another entry

     1. Subenum
     
        .. code:: markdown

            Some codeblock:
            ```python
            def main(argv): ...
            ```

     2. Another entry

Another subtitle
^^^^^^^^^^^^^^^^

Some code:

.. code:: python

    def main(argv):
        if argv[1] == 'help':
            print('Help!')

.. note::

  Some note.
  
  This note has two paragraphs.

A sub-sub-title
~~~~~~~~~~~~~~~

Some text...

  Some block quote.

    A nested block quote.

--------

Some unformatted code::

    foo bar!
    baz bam.
""",
        "restructuredtext",
        r"""# Main title


Some text\.
## Table of Contents

- [1   This is a subtitle](\#this\-is\-a\-subtitle)
- [2   Another subtitle](\#another\-subtitle)
  - [2\.1   A sub\-sub\-title](\#a\-sub\-sub\-title)
<a id="label"></a>
<a id="label-2"></a>
<a id="this-is-a-subtitle"></a>
## 1   This is a subtitle


Some test with <code>code</code>\.
Some <em>emphasis</em> and <strong>bold</strong> text\.

A [link](https\://ansible\.com/\))\.

A [reference](\#label)\.

A list\:
- Item 1\.
- Item 2\.
  
  This is still item 2\.
- Item 3\.

An enumeration\:
1. Entry 1
   
   More of Entry 1
1. Entry 2
1. Entry 3
   Second line of entry 3
   - Sublist
   - Another entry
     1. Subenum
        ````markdown
        Some codeblock:
        ```python
        def main(argv): ...
        ```
        ````
     1. Another entry
<a id="another-subtitle"></a>
## 2   Another subtitle


Some code\:
```python
def main(argv):
    if argv[1] == 'help':
        print('Help!')
```
> [!NOTE]
> 
> Some note\.
> 
> This note has two paragraphs\.
<a id="a-sub-sub-title"></a>
### 2\.1   A sub\-sub\-title


Some text\.\.\.
> 
> Some block quote\.
> > 
> > A nested block quote\.

---


Some unformatted code\:
```
foo bar!
baz bam.
```""",
        set(),
    ),
    (
        "system-messages",
        r"""
==========
Main title
==========

Some text.

.. Trigger a system message:

.. unknown-shit::

  Something.
""",
        "restructuredtext",
        r"""# Main title


Some text\.

<details>
<summary><strong>ERROR/3</strong> (&lt;string&gt;, line 10)</summary>


Unknown directive type \"unknown\-shit\"\.
```
.. unknown-shit::

  Something.
```

</details>""",
        set(),
    ),
    (
        "table",
        r""".. _tables:

======
Tables
======

Regular table:

+-----+-----+
| Foo | Bar |
+=====+=====+
| A   | B   |
+-----+-----+
| C   | D   |
|     | DD  |
|     | DDD |
+-----+-----+

A list table:

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Foo
    - Bar
  * - A
    - B
  * - C
    - D

      DD

      DDD
""",
        "restructuredtext",
        r"""# Tables

<a id="tables"></a>

Regular table\:

A list table\:""",
        {"table"},
    ),
]


@pytest.mark.parametrize(
    "title, input, input_parser, output, unsupported_class_names",
    RENDER_AS_MARKDOWN_AND_STRUCTURE_DATA,
    ids=[e[0] for e in RENDER_AS_MARKDOWN_AND_STRUCTURE_DATA],
)
def test_render_markdown(title, input, input_parser, output, unsupported_class_names):
    result = render_as_markdown(input, parser_name=input_parser)
    print(get_document_structure(input, parser_name=input_parser).output)
    assert result.output == output
    assert result.unsupported_class_names == unsupported_class_names
