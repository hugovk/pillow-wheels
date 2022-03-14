import os
import re
import urllib.request

import atoma

try:
    from rich import print
except ImportError:
    pass

DEFINITIONS_FILE = "config.sh"

DEPENDENCIES = [
    # Name, feed URL or GitHub slug, version prefix
    ("bzip2", "https://gitlab.com/bzip2/bzip2/-/tags?format=atom", "bzip2-"),
    ("freetype", "freetype/freetype", "VER-"),
    ("giflib", "https://libraries.io/conda/giflib/versions.atom", ""),
    ("harfbuzz", "harfbuzz/harfbuzz", ""),
    ("jpegturbo", "libjpeg-turbo/libjpeg-turbo", ""),
    ("lcms2", "mm2/Little-CMS", "lcms"),
    ("libpng", "glennrp/libpng", "v"),
    ("libwebp", "webmproject/libwebp", "v"),
    ("libxcb", "https://libraries.io/conda/libxcb/versions.atom", "v"),
    ("openjpeg", "uclouvain/openjpeg", "v"),
    ("tiff", "https://gitlab.com/libtiff/libtiff/-/tags?format=atom", "v"),
    ("xz", "libarchive/xz", "v"),
    ("zlib", "madler/zlib", "v"),
]


def feed_url(feed: str) -> str:
    if feed.startswith("https:"):
        return feed
    return f"https://github.com/{feed}/tags.atom"


def update_version(name: str, feed: str, version_prefix: str) -> str | None:
    url = feed_url(feed)
    print(url)
    contents = urllib.request.urlopen(url).read()
    feed = atoma.parse_atom_bytes(contents)
    link = feed.entries[0].links[0].href
    print(link)
    new_tag = link.rsplit("/", 1)[1]
    print(f"{new_tag=}")
    new_version = new_tag.removeprefix(version_prefix)
    # Special handling for FreeType tags, e.g. "VER-2-11-1"
    if name == "freetype":
        new_version = new_version.replace("-", ".")
    print(f"{new_version=}")

    with open(DEFINITIONS_FILE) as f:
        content = f.read()
        content_new = re.sub(
            # Skips lines version lines ending " # no-auto-bump"
            rf"{name.upper()}_VERSION=[\d.]+\n",
            f"{name.upper()}_VERSION={new_version}\n",
            content,
        )
    changes_made = content != content_new
    print(f"{changes_made=}")
    print()

    if changes_made:
        # Write the file out again
        with open(DEFINITIONS_FILE, "w") as f:
            f.write(content_new)
        return f"{name} to {new_version}"

    return None


def main() -> None:
    updates = []
    for name, feed, v_in_tag in DEPENDENCIES:
        update = update_version(name, feed, v_in_tag)
        if update:
            updates.append(update)

    if updates:
        commit_message = "Update " + ", ".join(updates)
        print(commit_message)

        github_env_file = os.getenv("GITHUB_ENV")
        if github_env_file:
            with open(github_env_file, "a") as f:
                f.write(f"COMMIT_MESSAGE={commit_message}")
    else:
        print("No updates")


if __name__ == "__main__":
    main()
