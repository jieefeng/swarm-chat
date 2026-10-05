"""测试公共配置：把仓库根目录加入 sys.path。

各测试文件通过 `from agenthub.backend...` 导入被测代码，该包路径
只有以仓库根为起点才能解析；没有这一步，`pytest tests/test_xxx.py`
单文件运行时会 ModuleNotFoundError。
"""
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)
