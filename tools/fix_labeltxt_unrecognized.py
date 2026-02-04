import argparse
import json
import os

TARGET_KEYS = {"vc_displace", "vc_emission_standard", "vc_carrying_num"}
TARGET_TEXTS = {"一", "—", "－", "–", "-"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label_txt", required=True, help="Path to Label.txt")
    args = parser.parse_args()

    if not os.path.exists(args.label_txt):
        raise FileNotFoundError(args.label_txt)

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
                output_lines.append(line)
                continue
            for item in items:
                key_cls = item.get("key_cls", "None")
                if key_cls in TARGET_KEYS:
                    text_val = str(item.get("transcription", "")).strip()
                    if text_val in TARGET_TEXTS:
                        item["transcription"] = "-"
            output_lines.append(img_path + "\t" + json.dumps(items, ensure_ascii=False))

    with open(args.label_txt, "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")

    print("Updated:", args.label_txt)


if __name__ == "__main__":
    main()
