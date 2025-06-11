# Web-to-App APK Builder

This project is a Streamlit-based tool that allows you to convert any website into an Android APK. It packages a WebView inside a native Android application and customizes it with your own app label, URL, package name, and icon.

## Features

- Generate Android APKs from any website URL  
- Customizable app name and icon  
- Dynamically applies unique package names (e.g., `com.yourname`)  
- Supports both `assembleDebug` and `assembleRelease` Gradle builds  
- Automatically removes old Java source folders to avoid build conflicts

## Requirements

- Python 3.8 or newer  
- Android SDK and Gradle (ensure `gradlew.bat` or `gradlew` is available)  
- Java JDK 8 or higher  
- Python packages:  
  - Pillow  
  - Streamlit  

Install dependencies:

```bash
pip install pillow streamlit
Running the App
Open your terminal and execute:
```

```bash
streamlit run streamlit_app.py
```
This will launch the web interface in your browser.

Usage
Enter your app label (e.g., My App)

Enter your website URL (e.g., https://example.com)

Enter a unique package name (e.g., myuniqueapp)

Upload an app icon (JPG, PNG, BMP, etc.)

Select build type: assembleDebug or assembleRelease

Click "Generate APK"

The built APK will be available for download once the process completes.