import streamlit as st
from pathlib import Path
import shutil
import os
import re
import subprocess
from PIL import Image, ImageDraw

# --- Constants ---
ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
JAVA_ACTIVITY = ROOT / "app/src/main/java/com/myexampoint/webtoapp/MainActivity.java"
MIPMAP_DIRS = [
    ROOT / f"app/src/main/res/mipmap-{dpi}"
    for dpi in ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"]
]
# mipmap-anydpi-v26 stays unchanged (contains XML references)

# --- Helpers ---
def make_rounded_icon(img: Image.Image) -> Image.Image:
    """Return a rounded‐corner version of img, preserving transparency."""
    size = img.size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    # radius = half of the smaller dimension for a fully circular mask
    radius = min(size) // 2
    draw.rounded_rectangle([0, 0, *size], radius=radius, fill=255)
    rounded = Image.new("RGBA", size)
    rounded.paste(img, (0, 0), mask=mask)
    return rounded

# --- UI ---
st.title("Web-to-App APK Builder")

label       = st.text_input("App Label (e.g., Shnuritek The Game)")
url         = st.text_input("Website URL (e.g., https://example.com)")
uploaded    = st.file_uploader("Upload App Icon", type=["jpg","jpeg","png","webp","bmp"])
build_type  = st.selectbox("Build Type", ["assembleDebug", "assembleRelease"])

if st.button("Generate APK"):
    if not all([label, url, uploaded]):
        st.error("All fields are required.")
        st.stop()

    # 1) Update AndroidManifest.xml
    st.info("Updating AndroidManifest.xml…")
    manifest = MANIFEST.read_text(encoding="utf-8")
    manifest = re.sub(
        r'android:label="[^"]*"',
        f'android:label="{label}"',
        manifest
    )
    MANIFEST.write_text(manifest, encoding="utf-8")

    # 2) Update MainActivity.java
    st.info("Updating MainActivity.java…")
    java = JAVA_ACTIVITY.read_text(encoding="utf-8")
    java = java.replace(
        'String myurl = "https://abduznik.github.io/tomermeme/";',
        f'String myurl = "{url}";'
    )
    JAVA_ACTIVITY.write_text(java, encoding="utf-8")

    # 3) Generate & copy icons
    st.info("Generating launcher icons…")
    img = Image.open(uploaded).convert("RGBA")
    fg = img.copy()                   # foreground = original
    rnd = make_rounded_icon(img)       # rounded version

    # Clean out existing launcher files (except anydpi XML)
    res_dir = ROOT / "app/src/main/res"
    for d in res_dir.iterdir():
        if d.is_dir() and d.name.startswith("mipmap-") and d.name != "mipmap-anydpi-v26":
            for f in d.glob("ic_launcher*"):
                f.unlink(missing_ok=True)

    # Save into each density folder
    for mipmap in MIPMAP_DIRS:
        mipmap.mkdir(parents=True, exist_ok=True)
        img.save(mipmap / "ic_launcher.png", "PNG")
        fg.save(mipmap / "ic_launcher_foreground.png", "PNG")
        rnd.save(mipmap / "ic_launcher_round.png", "PNG")

    # 4) Build APK
    st.info(f"Building APK ({build_type})… this may take a while.")
    cmd = (["gradlew.bat"] if os.name=="nt" else ["./gradlew"]) + [build_type]
    proc = subprocess.run(
        cmd, cwd=ROOT, capture_output=True, text=True,
        shell=(os.name=="nt")
    )

    if proc.returncode == 0:
        st.success("APK built successfully!")
        sub = ("app/build/outputs/apk/debug/app-debug.apk"
               if build_type=="assembleDebug"
               else "app/build/outputs/apk/release/app-release.apk")
        apk = ROOT / sub
        if apk.exists():
            st.download_button("Download APK", apk.read_bytes(), file_name="webtoapp.apk")
        else:
            st.warning("Built APK not found at expected location.")
    else:
        st.error("APK build failed.")
        st.text(proc.stdout)
        st.text(proc.stderr)
