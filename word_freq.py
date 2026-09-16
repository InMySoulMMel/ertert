"""Word frequency analysis of the first three chapters of "The Travels of Lao Can" (老残游记).

Cleans the source text (strips the table of contents, Liu E's self-preface,
Hu Shih's preface, and Liu E's chapter-end commentary marked with ※※※),
segments the remaining novel body with jieba, removes stop words and
single-character tokens, then writes the top 50 words to
frequency_results.txt and a bar chart of the top 20 to chart.png.
"""

import re
from collections import Counter
from pathlib import Path

import jieba
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "text.txt"
FREQ_OUTPUT = BASE_DIR / "frequency_results.txt"
CHART_OUTPUT = BASE_DIR / "chart.png"

TOP_N_RESULTS = 50
TOP_N_CHART = 20

# Chapter headings such as 第一回　土不制水历年成患　风能鼓浪到处可危
CHAPTER_HEADING_RE = re.compile(r"^第[一二三四五六七八九十百零]+回")
COMMENTARY_MARKER = "※※※"

# First three chapters only: keep from 第一回 up to (not including) 第四回
LAST_CHAPTER_PREFIX = "第四回"

CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# Built-in stop word list: common Chinese function words and grammatical
# particles (multi-character; single-character tokens are filtered by length).
STOP_WORDS = {
    "一个", "一些", "一下", "一时", "一面", "一边", "一般", "一样", "一齐",
    "一切", "一样儿", "我们", "你们", "他们", "她们", "它们", "咱们", "大家",
    "自己", "别人", "甚么", "什么", "怎么", "怎样", "如何", "多少", "几个",
    "这个", "那个", "这些", "那些", "这里", "那里", "这样", "那样", "这般",
    "那般", "这时", "那时", "当时", "此刻", "现在", "如今", "起来", "出来",
    "下来", "下去", "过来", "过去", "回来", "上去", "上来", "进来", "出去",
    "就是", "还是", "只是", "只有", "不过", "但是", "可是", "然而", "虽然",
    "因为", "所以", "于是", "因此", "然后", "已经", "曾经", "正在", "原来",
    "没有", "不能", "不得", "不见", "不曾", "不必", "不用", "可以", "能够",
    "应该", "须要", "有些", "有点", "几时", "哪里", "哪儿", "谁人",
    "如此", "如是",
}

# Candidate CJK fonts, tried in order until one is found on the system.
FONT_CANDIDATES = [
    "Noto Sans CJK SC",
    "Noto Sans CJK TC",
    "Noto Serif CJK SC",
    "WenQuanYi Zen Hei",
    "WenQuanYi Micro Hei",
    "SimHei",
    "Microsoft YaHei",
    "PingFang SC",
]


def clean_text(text: str) -> list[str]:
    """Return the novel body (first three chapters) as cleaned lines.

    Strips, in order:
      * the table of contents and everything before the first real chapter
        heading (this covers the TOC line, Liu E's self-preface, and Hu
        Shih's preface), and everything from 第四回 onwards (chapters 4-20);
      * every line from a ※※※ marker until the next chapter heading
        (Liu E's chapter-end commentary);
      * duplicated chapter-heading lines (the source prints each title twice).
    """
    body_lines: list[str] = []
    in_body = False      # reached the first chapter heading (第一回)
    in_commentary = False  # inside a ※※※ commentary block
    last_heading = None

    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("\ufeff").strip()
        if not line:
            continue

        if CHAPTER_HEADING_RE.match(line):
            if line.startswith(LAST_CHAPTER_PREFIX):
                break  # reached 第四回: keep only the first three chapters
            if line != last_heading:
                in_commentary = False  # a new chapter ends any commentary block
                last_heading = line
                in_body = True
                body_lines.append(line)
            continue  # skip duplicate heading lines

        if not in_body or in_commentary:
            continue

        if line.startswith(COMMENTARY_MARKER):
            in_commentary = True
            continue

        body_lines.append(line)

    return body_lines


def count_words(lines: list[str]) -> Counter:
    """Segment with jieba and count meaningful words."""
    text = "".join(lines)
    words = jieba.lcut(text)
    counter = Counter()
    for word in words:
        word = word.strip()
        if len(word) < 2:            # filter single-character tokens
            continue
        if word in STOP_WORDS:       # remove stop words
            continue
        if not CJK_RE.search(word):  # keep only tokens containing Chinese
            continue
        counter[word] += 1
    return counter


def configure_chinese_font() -> None:
    """Pick the first available CJK font so Chinese renders in the chart."""
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in FONT_CANDIDATES:
        if name in available:
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["font.sans-serif"] = [name]
            break
    else:
        print("Warning: no CJK font found; Chinese characters may not render.")
    plt.rcParams["axes.unicode_minus"] = False


def plot_top_words(counter: Counter, output_path: Path) -> None:
    top = counter.most_common(TOP_N_CHART)
    words = [w for w, _ in top]
    counts = [c for _, c in top]

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.bar(words, counts, color="#4C72B0", edgecolor="white")
    ax.set_title("《老残游记》前三回高频词 Top 20", fontsize=18, pad=15)
    ax.set_xlabel("词语", fontsize=13)
    ax.set_ylabel("出现次数", fontsize=13)
    ax.tick_params(axis="x", labelrotation=45, labelsize=12)
    ax.tick_params(axis="y", labelsize=11)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    text = INPUT_FILE.read_text(encoding="utf-8")
    body_lines = clean_text(text)
    print(f"Novel body after cleaning: {len(body_lines)} lines, "
          f"{sum(len(l) for l in body_lines)} characters")

    counter = count_words(body_lines)
    top = counter.most_common(TOP_N_RESULTS)

    with FREQ_OUTPUT.open("w", encoding="utf-8") as f:
        for rank, (word, count) in enumerate(top, start=1):
            f.write(f"{rank}\t{word}\t{count}\n")
    print(f"Wrote top {len(top)} words to {FREQ_OUTPUT.name}")

    configure_chinese_font()
    plot_top_words(counter, CHART_OUTPUT)
    print(f"Wrote bar chart to {CHART_OUTPUT.name}")


if __name__ == "__main__":
    main()
