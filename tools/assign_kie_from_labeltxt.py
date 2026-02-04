import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Box:
    idx: int
    text: str
    points: List[List[float]]
    minx: float
    miny: float
    maxx: float
    maxy: float
    cx: float
    cy: float
    h: float
    w: float


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    t = text.strip()
    # remove leading numbers and punctuation like "1.", "1、", "1)"
    t = re.sub(r"^\s*\d+\s*[\.、)）:：]\s*", "", t)
    # remove spaces and fullwidth spaces
    t = re.sub(r"[\s\u3000]+", "", t)
    return t


def build_box(idx: int, item: dict) -> Box:
    text = item.get("transcription", item.get("label", ""))
    points = item.get("points") or []
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    h = maxy - miny
    w = maxx - minx
    return Box(idx, text, points, minx, miny, maxx, maxy, cx, cy, h, w)


def vertical_overlap(a: Box, b: Box) -> float:
    return max(0.0, min(a.maxy, b.maxy) - max(a.miny, b.miny))


def same_row(a: Box, b: Box, min_overlap_ratio: float) -> bool:
    overlap = vertical_overlap(a, b)
    if overlap <= 0:
        return False
    denom = min(a.h, b.h) if min(a.h, b.h) > 0 else 1.0
    return (overlap / denom) >= min_overlap_ratio


def extract_inline_value(text: str, label_patterns: List[re.Pattern]) -> str:
    raw = text
    norm = normalize_text(raw)
    for pat in label_patterns:
        m = pat.search(norm)
        if m:
            # try removing the matched label from normalized text
            start, end = m.span()
            leftover = (norm[:start] + norm[end:]).strip()
            # also strip common separators
            leftover = leftover.strip(":：/\\-| ")
            return leftover
    return ""


def top_left_key(box: Box) -> Tuple[float, float]:
    return (box.cy, box.cx)


def is_key_label(text: str, all_label_patterns: List[re.Pattern]) -> bool:
    norm = normalize_text(text)
    return any(p.search(norm) for p in all_label_patterns)


def build_label_patterns(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(p) for p in patterns]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assign KIE key_cls to value boxes based on label boxes in PPOCRLabel Label.txt"
    )
    parser.add_argument("--label_txt", required=True, help="Path to Label.txt")
    parser.add_argument(
        "--output",
        default=None,
        help="Output Label.txt path (default: Label.kie.txt next to input)",
    )
    parser.add_argument("--min_x_gap", type=float, default=5.0, help="Min gap to the right")
    parser.add_argument(
        "--row_overlap", type=float, default=0.4, help="Min vertical overlap ratio"
    )
    args = parser.parse_args()

    label_txt = args.label_txt
    if not os.path.exists(label_txt):
        raise FileNotFoundError(label_txt)

    output = args.output
    if output is None:
        base_dir = os.path.dirname(label_txt)
        output = os.path.join(base_dir, "Label.kie.txt")

    # label specs: each entry maps a label box to N value boxes (value_keys length)
    label_specs = [
        {"patterns": [r"合格证编号"], "value_keys": ["vc_no"]},
        {"patterns": [r"发证日期"], "value_keys": ["vc_issue_date"]},
        {"patterns": [r"车辆制造企业名称"], "value_keys": ["vc_manu_enterprise"]},
        {
            "patterns": [r"车辆品牌/车辆名称", r"车辆品牌", r"车辆名称"],
            "value_keys": ["vc_brands", "vc_type"],
        },
        {"patterns": [r"车辆型号"], "value_keys": ["vc_model_no"]},
        {"patterns": [r"车辆识别代号/车架号", r"车架号"], "value_keys": ["vc_vin"]},
        {"patterns": [r"车身颜色"], "value_keys": ["vc_color"]},
        {"patterns": [r"发动机型号"], "value_keys": ["vc_engine_model_no"]},
        {"patterns": [r"发动机号"], "value_keys": ["vc_engineno"]},
        {"patterns": [r"燃料种类", r"燃料类型"], "value_keys": ["vc_fuel"]},
        {
            "patterns": [r"排量和功率", r"排量/功率", r"排量和功率（ml/kW）"],
            "value_keys": ["vc_displace", "vc_power"],
        },
        {"patterns": [r"排放标准"], "value_keys": ["vc_emission_standard"]},
        {"patterns": [r"油耗"], "value_keys": ["vc_fuel_consumption"]},
        {
            "patterns": [r"外廓尺寸", r"外阔尺寸"],
            "value_keys": [
                "vc_overall_dimensions",
                "vc_overall_dimensions",
                "vc_overall_dimensions",
            ],
        },
        {"patterns": [r"轮胎数"], "value_keys": ["vc_tire_count"]},
        {"patterns": [r"轮胎规格"], "value_keys": ["vc_tyre_size"]},
        {
            "patterns": [r"轮距", r"轮距（前/后）", r"轮距\(前/后\)"],
            "value_keys": ["vc_track", "vc_track"],
        },
        {"patterns": [r"轴距"], "value_keys": ["vc_wheelbase"]},
        {"patterns": [r"轴荷"], "value_keys": ["vc_axle_load"]},
        {"patterns": [r"轴数"], "value_keys": ["vc_axle_count"]},
        {"patterns": [r"转向形式"], "value_keys": ["vc_steering_type"]},
        {"patterns": [r"总质量"], "value_keys": ["vc_totalw"]},
        {"patterns": [r"整备质量"], "value_keys": ["vc_curbw"]},
        {"patterns": [r"额定载客"], "value_keys": ["vc_carrying_num"]},
        {"patterns": [r"最高设计车速"], "value_keys": ["vc_max_speed"]},
        {"patterns": [r"车辆制造日期"], "value_keys": ["vc_manu_date"]},
    ]

    compiled_specs = []
    all_label_patterns = []
    for spec in label_specs:
        pats = build_label_patterns([normalize_text(p) for p in spec["patterns"]])
        compiled_specs.append({"patterns": pats, "value_keys": spec["value_keys"]})
        all_label_patterns.extend(pats)

    def match_label_boxes(boxes: List[Box], patterns: List[re.Pattern]) -> List[Box]:
        matched = []
        for b in boxes:
            norm = normalize_text(b.text)
            if any(p.search(norm) for p in patterns):
                matched.append(b)
        matched.sort(key=top_left_key)
        return matched

    output_lines = []
    with open(label_txt, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if "\t" not in line:
                # skip malformed line
                continue
            img_path, json_str = line.split("\t", 1)
            try:
                items = json.loads(json_str)
            except json.JSONDecodeError:
                # skip malformed json
                continue
            boxes = [build_box(i, item) for i, item in enumerate(items)]
            key_flags = {b.idx: is_key_label(b.text, all_label_patterns) for b in boxes}

            out_items = []

            for spec in compiled_specs:
                label_boxes = match_label_boxes(boxes, spec["patterns"])
                if not label_boxes:
                    continue
                label_box = label_boxes[0]
                candidates = []
                for b in boxes:
                    if b.idx == label_box.idx:
                        continue
                    if key_flags.get(b.idx, False):
                        continue
                    if b.cx <= (label_box.maxx + args.min_x_gap):
                        continue
                    if same_row(label_box, b, args.row_overlap):
                        candidates.append(b)
                candidates.sort(key=lambda b: b.cx)

                value_keys = spec["value_keys"]
                if candidates:
                    for i, key in enumerate(value_keys):
                        if i >= len(candidates):
                            break
                        b = candidates[i]
                        out_items.append(
                            {
                                "transcription": b.text,
                                "points": b.points,
                                "difficult": False,
                                "key_cls": key,
                            }
                        )
                else:
                    # fallback: inline value in label box
                    inline_value = extract_inline_value(label_box.text, spec["patterns"])
                    if inline_value:
                        out_items.append(
                            {
                                "transcription": inline_value,
                                "points": label_box.points,
                                "difficult": False,
                                "key_cls": value_keys[0],
                            }
                        )

            # sort output by position for readability
            out_items.sort(key=lambda it: (min(p[1] for p in it["points"]), min(p[0] for p in it["points"])))
            output_lines.append(
                img_path + "\t" + json.dumps(out_items, ensure_ascii=False)
            )

    with open(output, "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")

    print(f"Saved: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
