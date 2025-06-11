import streamlit as st
from pathlib import Path
import shutil
import os
import re
import subprocess
from PIL import Image, ImageDraw
import stat
import time

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
MAIN_ACTIVITY = ROOT / "MainActivity.java"
BUILD_GRADLE = ROOT / "app/build.gradle"
MIPMAP_DIRS = [ROOT / f"app/src/main/res/mipmap-{dpi}" for dpi in ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"]]
JAVA_SRC_DIR = ROOT / "app/src/main/java"

def make_rounded_icon(img: Image.Image) -> Image.Image:
    size = img.size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    radius = min(size) // 2
    draw.rounded_rectangle([0, 0, *size], radius=radius, fill=255)
    rounded = Image.new("RGBA", size)
    rounded.paste(img, (0, 0), mask=mask)
    return rounded

def on_rm_error(func, path, exc_info):
    if func in (os.rmdir, os.remove, os.unlink):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    else:
        raise

st.title("Web-to-App APK Builder")

label = st.text_input("App Label (e.g., My App)")
url = st.text_input("Website URL (e.g., https://example.com)")
package_name = st.text_input("Package name (e.g., myapp123)")
uploaded = st.file_uploader("Upload App Icon", type=["jpg", "jpeg", "png", "webp", "bmp"])
build_type = st.selectbox("Build Type", ["assembleDebug", "assembleRelease"])

if st.button("Generate APK"):
    if not all([label, url, package_name, uploaded]):
        st.error("All fields are required.")
        st.stop()

    full_package = f"com.{package_name}"
    st.info(f"Using package name: {full_package}")

    # Update AndroidManifest.xml
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    manifest_text = re.sub(r'package="[^"]+"', f'package="{full_package}"', manifest_text)
    manifest_text = re.sub(r'android:label="[^"]*"', f'android:label="{label}"', manifest_text)
    MANIFEST.write_text(manifest_text, encoding="utf-8")

    # Update applicationId in build.gradle
    gradle_text = BUILD_GRADLE.read_text(encoding="utf-8")
    gradle_text = re.sub(r'applicationId\s+"[^"]+"', f'applicationId "{full_package}"', gradle_text)
    BUILD_GRADLE.write_text(gradle_text, encoding="utf-8")

    # Remove old Java package directory
    java_package_root = JAVA_SRC_DIR / "com"
    if java_package_root.exists():
        for i in range(5):
            try:
                shutil.rmtree(java_package_root, onerror=on_rm_error)
                break
            except PermissionError:
                time.sleep(1)
        else:
            st.error(f"Failed to delete {java_package_root}.")
            st.stop()

    # Create new Java package directory
    new_package_dir = JAVA_SRC_DIR / "com" / package_name
    new_package_dir.mkdir(parents=True, exist_ok=True)

    # Copy and modify MainActivity.java
    main_code = MAIN_ACTIVITY.read_text(encoding="utf-8")
    main_code = re.sub(
        r'package\s+[^;]+;',
        f'package {full_package};',
        main_code
    )
    main_code = re.sub(
        r'String\s+myurl\s*=\s*".*?";',
        f'String myurl = "{url}";',
        main_code
    )
    (new_package_dir / "MainActivity.java").write_text(main_code, encoding="utf-8")

    # Generate icons
    img = Image.open(uploaded).convert("RGBA")
    fg = img.copy()
    rnd = make_rounded_icon(img)

    res_dir = ROOT / "app/src/main/res"
    for d in res_dir.iterdir():
        if d.is_dir() and d.name.startswith("mipmap-") and d.name != "mipmap-anydpi-v26":
            for f in d.glob("ic_launcher*"):
                f.unlink(missing_ok=True)

    for mipmap in MIPMAP_DIRS:
        mipmap.mkdir(parents=True, exist_ok=True)
        img.save(mipmap / "ic_launcher.png", "PNG")
        fg.save(mipmap / "ic_launcher_foreground.png", "PNG")
        rnd.save(mipmap / "ic_launcher_round.png", "PNG")

    # Clean project
    clean_cmd = (["gradlew.bat"] if os.name == "nt" else ["./gradlew"]) + ["clean"]
    st.info("Cleaning previous build artifacts...")
    clean_proc = subprocess.run(clean_cmd, cwd=ROOT, capture_output=True, text=True, shell=(os.name == "nt"))
    if clean_proc.returncode != 0:
        st.error("Clean failed.")
        st.text(clean_proc.stdout)
        st.text(clean_proc.stderr)
        st.stop()

    # Build APK
    st.info(f"Building APK ({build_type})… this may take a while.")
    build_cmd = (["gradlew.bat"] if os.name == "nt" else ["./gradlew"]) + [build_type]
    proc = subprocess.run(build_cmd, cwd=ROOT, capture_output=True, text=True, shell=(os.name == "nt"))

    if proc.returncode == 0:
        st.success("APK built successfully!")
        apk_path = ROOT / ("app/build/outputs/apk/debug/app-debug.apk" if build_type == "assembleDebug" else "app/build/outputs/apk/release/app-release.apk")
        if apk_path.exists():
            st.download_button("Download APK", apk_path.read_bytes(), file_name=f"{package_name}.apk")
        else:
            st.warning("Built APK not found at expected location.")
    else:
        st.error("APK build failed.")
        st.text(proc.stdout)
        st.text(proc.stderr)
