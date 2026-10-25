"""包冒烟测试：模块可导入（实现主体是 TODO 占位，先锁包结构）。"""
import campus_planning.amap_client  # noqa: F401
import campus_planning.route_converter  # noqa: F401
import campus_planning.goal_server  # noqa: F401


def test_entry_points_defined():
    import setuptools
    import os
    setup_py = os.path.join(os.path.dirname(__file__), '..', 'setup.py')
    content = open(setup_py, encoding='utf-8').read()
    assert 'amap_client' in content
    assert 'route_converter' in content
    assert 'goal_server' in content
