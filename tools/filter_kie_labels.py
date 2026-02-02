import argparse
import json
import os

KEEP_KEYS = {
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


def filter_file(path):
    if not os.path.exists(path):
        return False
    out_lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if "\t" not in line:
                continue
            img_path, json_str = line.split("\t", 1)
            try:
                items = json.loads(json_str)
            except json.JSONDecodeError:
                continue
            kept = []
            for item in items:
                key_cls = item.get("key_cls", "None")
                if key_cls in KEEP_KEYS:
                    kept.append(item)
            out_lines.append(img_path + "\t" + json.dumps(kept, ensure_ascii=False))
    with open(path, "w", encoding="utf-8") as f:
        for line in out_lines:
            f.write(line + "\n")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="folder containing Label.txt/Cache.cach")
    args = parser.parse_args()

    base = args.dir
    label_path = os.path.join(base, "Label.txt")
    cache_path = os.path.join(base, "Cache.cach")

    ok1 = filter_file(label_path)
    ok2 = filter_file(cache_path)
    print("filtered:", label_path if ok1 else "(missing)", ",", cache_path if ok2 else "(missing)")


if __name__ == "__main__":
    main()