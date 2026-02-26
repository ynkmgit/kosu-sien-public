"""加重平均進捗率の計算テスト"""
from routers.common.assignment_grid_renderer import _calc_weighted_progress


def test_all_none():
    """全員進捗未入力→None"""
    assert _calc_weighted_progress([(None, 10), (None, 20)]) is None


def test_empty_list():
    """担当者なし→None"""
    assert _calc_weighted_progress([]) is None


def test_weighted_average():
    """山積計による加重平均"""
    # 担当A: 50%, 山積10h / 担当B: 100%, 山積30h
    # = (50*10 + 100*30) / (10+30) = 3500/40 = 87.5 → 88
    result = _calc_weighted_progress([(50, 10), (100, 30)])
    assert result == 88


def test_zero_weights_fallback():
    """山積計が全て0→単純平均"""
    # 担当A: 40%, 山積0h / 担当B: 80%, 山積0h
    # = (40+80) / 2 = 60
    result = _calc_weighted_progress([(40, 0), (80, 0)])
    assert result == 60


def test_partial_progress():
    """一部の担当者のみ進捗入力済み"""
    # 担当A: 50%, 山積10h / 担当B: None, 山積20h
    # Noneは除外 → 50
    result = _calc_weighted_progress([(50, 10), (None, 20)])
    assert result == 50


def test_single_assignee():
    """1名でも正しく動作"""
    assert _calc_weighted_progress([(75, 10)]) == 75


def test_equal_weights():
    """等しい山積計→単純平均と同等"""
    # 担当A: 30%, 山積10h / 担当B: 70%, 山積10h
    # = (30*10 + 70*10) / 20 = 50
    result = _calc_weighted_progress([(30, 10), (70, 10)])
    assert result == 50
