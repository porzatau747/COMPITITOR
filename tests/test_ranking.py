from app.services.scoring_service import final_score


def test_local_relevance_prevents_big_meme_from_winning():
    useful_it = final_score(600, 90, 90, 100)
    big_meme = final_score(5000, 10, 90, 100)
    assert useful_it > big_meme
