#!/usr/bin/env python3
import csv
import argparse
import subprocess
import tempfile
import os
import re
from PIL import Image, ImageDraw, ImageFont

def main():
    parser = argparse.ArgumentParser(description="Generate group QR codes from CSV.")
    parser.add_argument("-g", "--group", type=int, required=True, help="Group number")
    parser.add_argument("-s", "--sheet", type=int, required=True, help="Sheet number")
    parser.add_argument("-f", "--file", type=str, default="data.csv", help="Input CSV file")
    parser.add_argument("-o", "--output", type=str, default="qrcodes.png", help="Output PNG file")
    parser.add_argument("-d", "--display", help="Display image when created", action='store_true')
    args = parser.parse_args()

    if not (2 <= args.sheet <= 8):
        raise ValueError("!!! Sheet must be between 2 and 8 !!!")

    group_num = args.group
    sheet_col = f"sheet{args.sheet}"

    with open(args.file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = []
        for row in reader:
            gruppe_field = row["Gruppe"].strip()
            match = re.search(r"Gruppe .(\d+)", gruppe_field)
            if match and int(match.group(1)) == group_num:
                rows.append(row)

    if not rows:
        print(f" !!! No entries found for group I{group_num}. !!!")
        return

    qr_images = []
    tmpfiles = []

    try:
        for row in rows[:3]:  # max 3 QR codes
            token = row.get(sheet_col, "").strip()
            if not token:
                continue

            url = f"https://judge.acps.tuhh.de/questions/{token}"
            tmp_png = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmpfiles.append(tmp_png.name)

            subprocess.run(
                ["qr", f"--output={tmp_png.name}", url],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )

            name = f"{row['Vorname']} {row['Nachname']}".strip()
            qr_img = Image.open(tmp_png.name).convert("RGBA")

            font = ImageFont.load_default()
            draw_tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            bbox_default = draw_tmp.textbbox((0, 0), name, font=font)
            default_height = bbox_default[3] - bbox_default[1]

            try:
                font_scalar = 3.0
                target_size = max(1, int(round(default_height * font_scalar)))
                font = ImageFont.truetype("DejaVuSans.ttf", target_size)
            except:
                pass

            bbox = draw_tmp.textbbox((0, 0), name, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            new_img = Image.new("RGBA", (qr_img.width, qr_img.height + text_height + 10), "white")
            draw = ImageDraw.Draw(new_img)
            draw.text(((qr_img.width - text_width) / 2, 2), name, fill="black", font=font)
            new_img.paste(qr_img, (0, text_height + 10))


            qr_images.append(new_img)

        if not qr_images:
            print(f"!!! No valid tokens found for sheet {args.sheet} in group I{group_num}. !!!")
            return

        total_width = sum(img.width for img in qr_images) + (len(qr_images) - 1) * 20
        max_height = max(img.height for img in qr_images)
        combined = Image.new("RGBA", (total_width, max_height), "white")

        x = 0
        for img in qr_images:
            combined.paste(img, (x, 0))
            x += img.width + 20

        combined.save(args.output)
        print(f"✓ saved: {args.output} ✓")

    finally:
        for f in tmpfiles:
            try:
                os.remove(f)
            except OSError:
                pass
        if args.display:
            if os.name == 'nt':
                subprocess.run(
                    [args.output],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
            else:
                subprocess.run(
                    ["open", args.output],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )

if __name__ == "__main__":
    main()
