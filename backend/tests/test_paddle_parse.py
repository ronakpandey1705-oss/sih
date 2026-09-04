from app.services.ocr.paddle_ocr import parse_paddle_ocr_results


def test_parse_classic_paddle_list_of_lines():
    results = [[
        [[[10, 10], [80, 10], [80, 30], [10, 30]], ("MRP Rs. 50.00", 0.97)],
        [[[10, 40], [90, 40], [90, 60], [10, 60]], ("Net Qty: 200 g", 0.95)],
    ]]
    lines = parse_paddle_ocr_results(results, "img-1")
    assert [item["text"] for item in lines] == ["MRP Rs. 50.00", "Net Qty: 200 g"]
    assert lines[0]["bbox"] == [10, 10, 80, 30]
    assert lines[0]["image_id"] == "img-1"
    assert lines[0]["confidence"] == 0.97


def test_parse_classic_flat_page_without_outer_wrap():
    results = [
        [[[1, 1], [2, 1], [2, 2], [1, 2]], ("Mfd: 06/2026", 0.91)],
    ]
    lines = parse_paddle_ocr_results(results, "img-2")
    assert len(lines) == 1
    assert lines[0]["text"] == "Mfd: 06/2026"


def test_parse_paddle3_rec_texts_dict():
    results = [{
        "rec_texts": ["DemoBakes biscuits", "MRP Rs. 50.00"],
        "rec_scores": [0.99, 0.88],
        "rec_boxes": [[0, 0, 40, 12], [0, 14, 50, 26]],
        "rec_polys": [
            [[0, 0], [40, 0], [40, 12], [0, 12]],
            [[0, 14], [50, 14], [50, 26], [0, 26]],
        ],
    }]
    lines = parse_paddle_ocr_results(results, "img-3")
    assert [item["text"] for item in lines] == ["DemoBakes biscuits", "MRP Rs. 50.00"]
    assert lines[1]["bbox"] == [0, 14, 50, 26]


class _PaddleResult:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


def test_parse_does_not_treat_lists_as_dicts():
    # Lists implement __getitem__; calling .get would throw and empty the OCR path.
    results = [[[ [[5, 5], [15, 5], [15, 9], [5, 9]], ("Consumer Care: 1800", 0.93) ]]]
    lines = parse_paddle_ocr_results(results, "img-4")
    assert len(lines) == 1
    assert "1800" in lines[0]["text"]


def test_parse_paddle_result_object_with_get():
    results = [_PaddleResult({
        "rec_texts": ["Unit Sale Price Rs. 0.25 / g"],
        "rec_scores": [0.8],
        "rec_boxes": [[2, 2, 20, 8]],
        "rec_polys": [],
    })]
    lines = parse_paddle_ocr_results(results, "img-5")
    assert lines[0]["text"].startswith("Unit Sale Price")


def test_parse_numpy_rec_arrays_without_truthiness():
    import numpy as np

    results = [{
        "rec_texts": ["MRP Rs 10"],
        "rec_scores": np.array([0.999], dtype=np.float32),
        "rec_boxes": np.array([[8, 12, 120, 40]], dtype=np.int32),
        "rec_polys": np.array([[[8, 12], [120, 12], [120, 40], [8, 40]]], dtype=np.int32),
    }]
    lines = parse_paddle_ocr_results(results, "img-np")
    assert len(lines) == 1
    assert lines[0]["text"] == "MRP Rs 10"
    assert lines[0]["bbox"] == [8, 12, 120, 40]
    assert lines[0]["polygon"][0] == [8, 12]
