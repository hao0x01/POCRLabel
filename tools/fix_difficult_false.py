import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser(
        description="Set all 'difficult' flags to false in Label.txt"
    )
    parser.add_argument("--label_txt", required=True, help="Path to Label.txt")
    args = parser.parse_args()

    if not os.path.exists(args.label_txt):
        raise FileNotFoundError(args.label_txt)

    updated_lines = []
    changed = 0

    with open(args.label_txt, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if "\t" not in line:
                updated_lines.append(line)
                continue
            img, js = line.split("\t", 1)
            try:
                items = json.loads(js)
            except Exception:
                # Keep original if parse fails
                updated_lines.append(line)
                continue
            for item in items:
                if item.get("difficult") is True:
                    item["difficult"] = False
                    changed += 1
            updated_lines.append(img + "\t" + json.dumps(items, ensure_ascii=False))

    with open(args.label_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines) + "\n")

    print(f"Updated: {args.label_txt}")
    print(f"Changed difficult flags: {changed}")


if __name__ == "__main__":
    main()
