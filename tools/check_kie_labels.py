import argparse
import json
import os

ALLOWED_KEYS = {
    "vc_no",
    "vc_issue_date",
    "vc_manu_enterprise",
    "vc_brands",
    "vc_type",
    "vc_model_no",
    "vc_vin",
    "vc_color",
    "vc_engineno",
    "vc_fuel",
    "vc_displace",
    "vc_power",
    "vc_emission_standard",
    "vc_tyre_size",
    "vc_wheelbase",
    "vc_totalw",
    "vc_curbw",
    "vc_carrying_num",
    "vc_manu_date",
    "vc_manu_addr",
}

UNRECOGNIZED_TEXTS = {"待识别", ""}


def main():
    parser = argparse.ArgumentParser(
        description="Check Label.txt for duplicate or invalid key_cls per image."
    )
    parser.add_argument("--label_txt", required=True, help="Path to Label.txt")
    parser.add_argument(
        "--allow_none", action="store_true", help="Ignore key_cls == None"
    )
    parser.add_argument(
        "--dedup",
        action="store_true",
        help="Deduplicate entries with same key_cls and transcription",
    )
    args = parser.parse_args()

    if not os.path.exists(args.label_txt):
        raise FileNotFoundError(args.label_txt)

    bad_images = []
    output_lines = []
    with open(args.label_txt, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or "\t" not in line:
                continue
            img_path, json_str = line.split("\t", 1)
            try:
                items = json.loads(json_str)
            except json.JSONDecodeError:
                bad_images.append((img_path, ["invalid_json"]))
                continue

            reasons = []
            seen = {}
            counts = {}
            dedup_items = []
            dedup_seen = set()
            for item in items:
                key_cls = item.get("key_cls", "None")
                text_val = str(item.get("transcription", "")).strip()
                if args.dedup:
                    dedup_key = (key_cls, text_val)
                    if dedup_key in dedup_seen:
                        continue
                    dedup_seen.add(dedup_key)
                    dedup_items.append(item)
                if key_cls == "None" and args.allow_none:
                    continue
                if key_cls != "None" and key_cls not in ALLOWED_KEYS:
                    reasons.append(f"invalid_key:{key_cls}")
                if key_cls != "None":
                    if key_cls not in seen:
                        seen[key_cls] = set()
                        counts[key_cls] = {}
                    seen[key_cls].add(text_val)
                    counts[key_cls][text_val] = counts[key_cls].get(text_val, 0) + 1
                if text_val in UNRECOGNIZED_TEXTS:
                    reasons.append(f"unrecognized_value:{key_cls}")

            for k, vals in seen.items():
                if len(vals) > 1:
                    reasons.append(f"duplicate_key:{k}")
                else:
                    # same value repeated
                    only_val = next(iter(vals)) if vals else ""
                    if only_val in counts.get(k, {}) and counts[k][only_val] > 1:
                        reasons.append(f"duplicate_same:{k}")

            if reasons:
                bad_images.append((img_path, reasons))
            if args.dedup:
                output_lines.append(
                    img_path + "\t" + json.dumps(dedup_items, ensure_ascii=False)
                )

    for img, reasons in bad_images:
        cn_reasons = []
        for r in sorted(set(reasons)):
            if r.startswith("invalid_key:"):
                cn_reasons.append("不在关键词中:" + r.split(":", 1)[1])
            elif r.startswith("duplicate_key:"):
                cn_reasons.append("重复标注:" + r.split(":", 1)[1])
            elif r.startswith("duplicate_same:"):
                cn_reasons.append("重复同值(可清理):" + r.split(":", 1)[1])
            elif r.startswith("unrecognized_value:"):
                cn_reasons.append("未识别:" + r.split(":", 1)[1])
            else:
                cn_reasons.append(r)
        print(img + "\t" + "，".join(cn_reasons))

    if args.dedup and output_lines:
        with open(args.label_txt, "w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")


if __name__ == "__main__":
    main()
