"""ドメイン例外定義"""


class DuplicateCodeError(Exception):
    """一意制約違反（CDの重複など）"""

    def __init__(self, message: str = "このコードは既に使用されています"):
        self.message = message
        super().__init__(self.message)
