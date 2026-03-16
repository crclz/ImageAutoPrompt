from entropy.domain.services.tag_checker import TagChecker


def test_extract_all_tags_basic_normalization():
    # 场景 1：基础空格处理、空格转下划线、去重
    s = "1girl, reading a book,   highres, reading_a_book"
    # 预期：空格转为下划线，"reading a book" 和 "reading_a_book" 视为同一个并去重
    expected = ["1girl", "reading_a_book", "highres"]
    assert TagChecker.extract_all_tags(s) == expected


def test_extract_all_tags_weight_stripping():
    # 场景 2：多层嵌套括号和方括号权重剥离
    s = "((1girl)), [sketch], (((masterpiece))), [[absurdres]]"
    # 预期：所有的 () 和 [] 应该被完全剥离，只剩下核心 Tag
    expected = ["1girl", "sketch", "masterpiece", "absurdres"]
    assert TagChecker.extract_all_tags(s) == expected


def test_extract_all_tags_numeric_weights():
    # 场景 3：数值权重格式 (tag:weight)
    s = "(best quality:1.4), (solo:0.8), [bad anatomy:1.2], sunset:1.5"
    # 预期：冒号及其后的数字权重应被移除
    expected = ["best_quality", "solo", "bad_anatomy", "sunset"]
    assert TagChecker.extract_all_tags(s) == expected


def test_extract_all_tags_escaped_characters():
    # 场景 4：最难处理的 Danbooru 特色转义括号（角色和作品名）
    # 注意：这里的反斜杠在 Python 字符串中需要转义或者用 raw string
    s = r"keqing \(genshin_impact\), (raiden_shogun_\(genshin_impact\):1.2)"
    # 预期：外层权重括号剥离，内层转义括号保留（去斜杠），空格转下划线
    expected = ["keqing_(genshin_impact)", "raiden_shogun_(genshin_impact)"]
    assert TagChecker.extract_all_tags(s) == expected


def test_extract_all_tags_sd_special_syntax():
    # 场景 5：排除 SD 特殊语法（如 LoRA）和处理 Prompt Editing
    s = "<lora:style_offset:1>, <hypernet:face:0.5>, [blue hair:red hair:0.2], 1girl"
    # 预期：LoRA 等被过滤，Prompt Editing 语法暂时作为整体保留（或根据你的需求调整）
    # 根据之前提供的代码逻辑，它会保留 [blue hair:red hair:0.2] 剥离后的内容
    expected = ["blue_hair:red_hair", "1girl"]
    assert TagChecker.extract_all_tags(s) == expected


def test_extract_all_tags_messy_input():
    # 场景 6：极端糟糕的输入（空项、多余逗号、换行、首尾下划线）
    s = """
    , , masterpiece, 
    
    (extremely_detailed_CG),,,
    __solo__
    """
    # 预期：自动忽略空字符串，处理换行，修剪下划线
    expected = ["masterpiece", "extremely_detailed_CG", "solo"]
    assert TagChecker.extract_all_tags(s) == expected


def test_tag_checker_happy_1():
    s = r"""
    1girl, reading a red book, book, masterpiece, sunset:1.2, keqing \(genshin_impact\):1.5, ganyu \(genshin_impact\),
    keqing_(genshin_impact), ((masterpiece, absurdres)), atdan, artist:atdan
    """
    not_exist_tags = TagChecker.get_not_exist_tags(s)

    assert ["reading a red book"] == not_exist_tags
