"""Milestone badge on every post (owner 25 Nov, his design): "SUBSCRIBERS RIGHT NOW 1,499 · BE THE 1,500TH!" with an
arrow down to the Subscribe/Follow button. The number is always one below the next 500 above the real count
(1,410 -> 1,499; 1,960 -> 1,999). Reels use YouTube subscribers, photos (FB + IG only) use Instagram followers.
Added once per file (.sub marker), like motion.progress_bar.
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

_COUNTS = {}


def milestone(n, step=500):
    return (n // step + 1) * step


def count(kind):
    if kind not in _COUNTS:
        from fmm import poster
        if kind == "yt":
            from fmm import youtube
            st = youtube.service().channels().list(mine=True, part="statistics").execute()["items"][0]["statistics"]
            _COUNTS[kind] = int(st["subscriberCount"])
        else:
            _COUNTS[kind] = int(poster.call("GET", poster.IG, params={"fields": "followers_count"})["followers_count"])
    return _COUNTS[kind]


def overlay(size, n, label, arrow=True):
    from fmm import brand
    W, H = size
    img = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    goal = milestone(n)
    s = W / 1080
    if not arrow:  # photo (FB/IG feed, 4:5): small pill top-right, the one corner our designs leave empty
        f = brand.label_font(int(30 * s))
        t = f"{goal - 1:,} FOLLOWERS  •  BE THE {goal:,}TH!"
        w = d.textlength(t, font=f)
        x1, y0 = W - 24 * s, 22 * s
        d.rounded_rectangle((x1 - w - 40 * s, y0, x1, y0 + 56 * s), int(28 * s), fill=(10, 10, 10, 230), outline=(255, 0, 0), width=max(2, int(4 * s)))
        d.text((x1 - w - 20 * s, y0 + 28 * s), t, font=f, fill=(255, 215, 0), anchor="lm")
        return img
    # Reels/Shorts (owner 25 Nov): right above the Subscribe/Follow button. On a 1080x1920 Short the channel row is
    # y ~1650-1715 with the avatar + @name at x ~40-330 and Subscribe right of the name (x ~340-540); the arrow tip
    # lands on the button centre. Measured from the owner's phone screenshot.
    bx, by = 411 * s, 1674 * s           # owner-approved 26 Nov after 7 private tests: tip just right of @FC_FMM (Subscribe)
    x0, y0 = int(151 * s), int(1464 * s)
    x1, y1 = int(751 * s), int(1614 * s)
    d.rounded_rectangle((x0, y0, x1, y1), int(26 * s), fill=(10, 10, 10, 230), outline=(255, 0, 0), width=max(2, int(5 * s)))
    d.text((x0 + 24 * s, y0 + 14 * s), label, font=brand.label_font(int(26 * s)), fill=(255, 255, 255))
    d.text((x0 + 24 * s, y0 + 44 * s), f"{goal - 1:,}", font=brand.font("Anton-Regular.ttf", int(74 * s)), fill=(255, 215, 0))
    d.text((x0 + 250 * s, y0 + 62 * s), f"BE THE {goal:,}TH!", font=brand.label_font(int(30 * s)), fill=(200, 255, 0))
    d.text((x0 + 250 * s, y0 + 100 * s), "TAP SUBSCRIBE", font=brand.label_font(int(24 * s)), fill=(255, 255, 255))
    d.rectangle((bx - 9 * s, y1, bx + 9 * s, by - 34 * s), fill=(255, 0, 0))
    d.polygon([(bx - 30 * s, by - 36 * s), (bx + 30 * s, by - 36 * s), (bx, by)], fill=(255, 0, 0))
    return img


def add(media, kind):
    """kind 'reel' (mp4, YouTube count) or 'photo' (image, Instagram count). Never blocks a post."""
    media = Path(media)
    mark = media.with_name(media.name + ".sub")
    if mark.exists():
        return media
    if kind == "photo":
        im = Image.open(media).convert("RGBA")
        im.alpha_composite(overlay(im.size, count("ig"), "FOLLOWERS RIGHT NOW", arrow=False))
        im.convert("RGB").save(media, quality=95)
    else:
        png = media.with_name(media.stem + "_sub.png")
        overlay((1080, 1920), count("yt"), "SUBSCRIBERS RIGHT NOW").save(png)
        tmp = media.with_name(media.stem + "_subtmp.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(media), "-i", str(png), "-filter_complex",
                        "[0:v]scale=1080:1920,setsar=1[v];[v][1:v]overlay=0:0,format=yuv420p[o]", "-map", "[o]", "-map",
                        "0:a?", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "copy", "-movflags",
                        "+faststart", str(tmp)], check=True)
        tmp.replace(media)
        png.unlink()
    mark.touch()
    return media


if __name__ == "__main__":
    assert milestone(1410) == 1500 and milestone(1499) == 1500 and milestone(1500) == 2000 and milestone(1960) == 2000
    print("ok")
