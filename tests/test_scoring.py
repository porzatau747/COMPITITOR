from app.services.scoring_service import calculate_raw_viral_score, local_relevance_score, final_score


def test_raw_viral_score_weights_engagement():
    assert calculate_raw_viral_score(10, 2, 1, 100) == 31


def test_local_relevance_scores_shop_categories_high_and_mobile_low():
    high = local_relevance_score("โน้ตบุ๊กทำงาน RAM SSD printer ซ่อมคอม")
    low = local_relevance_score("มือถือ เคสโทรศัพท์ ดราม่าแบรนด์")
    assert high >= 80
    assert low <= 30


def test_final_score_combines_required_weights():
    assert final_score(2, 80, 90, 70) == 48.8
