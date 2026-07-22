import scraper

def test_parse_race():
    d = scraper._parse_race("4007승 4220패(48.7%)")
    assert d == {"wins": 4007, "losses": 4220, "winrate": 48.7}

def test_parse_race_empty():
    assert scraper._parse_race("无数据")["winrate"] == 0.0

def test_balance_score_balanced():
    sc = scraper.balance_score(50, 50, 50, 1000)
    assert sc == 100.0

def test_balance_score_imbalanced():
    sc = scraper.balance_score(60, 45, 40, 1000)
    assert sc < 100

def test_balance_score_low_sample():
    assert scraper.balance_score(50, 50, 50, 10) is None  # 样本不足

def test_normalize_name_space():
    assert scraper.normalize_name("백 룸") == scraper.normalize_name("백룸")