# RetroScraper
<p align="center"><img width="902" height="697" alt="image" src="https://github.com/user-attachments/assets/79cb5160-afc8-47ce-9f50-de3b62e733a4" /></p>


RetroScraper is a user-friendly desktop application designed to automatically scan your retro game libraries, download high-quality metadata and artwork, and generate the gamelist.xml files needed by front-ends like EmulationStation.

Its main goal is to simplify the setup process for ArkOS devices, but it should work well with any other operating system that uses the standard EmulationStation folder structure (e.g., ROCKNIX, Knulli).

# ✨ Key Features

- Automatic Metadata Scraping: Downloads detailed game information including descriptions, release dates, genres, developers, publishers, and ratings from the LaunchBox Games Database.
- Artwork Downloader: Fetches three types of artwork for each game:
    - Thumbnail: Box art (Box - Front).
    - Image: A gameplay screenshot (Screenshot - Gameplay).
    - Marquee: The game's clear logo.
- ArkOS & EmulationStation Ready: Generates properly formatted gamelist.xml files and organizes downloaded images into an images subfolder within each system's ROM directory.
- Intelligent Matching: Uses a fuzzy matching algorithm to find the correct metadata for your ROMs, even if the filenames aren't perfect.
- Safe & Reversible: Automatically creates a backup (gamelist.xml.bak) of your existing gamelists before making any changes.
- Exclusion List: If a game can't be found in the database, it's added to an Excluded_From_Scan.txt file to prevent it from being repeatedly scanned.
- User-Friendly GUI: A simple interface lets you select your folder and start scanning with just a few clicks.

# ⚙️ How It Works

The application scans a main ROMs folder you select. It looks for subfolders that match the names of supported retro consoles (like snes, psx, gbc, etc.).
It also works if you only want to scan a single console folder.
For each system folder found, RetroScraper will:

- Identify all the game files (e.g., .zip, .sfc, .chd).
- Compare each game's filename against the LaunchBox metadata database to find a match.
- Create or update a gamelist.xml file with the game's metadata.
- Download the corresponding box art, screenshot, and logo into a newly created images subfolder.

# 🛠️ Building Binaries
📋 Requirements

    Python 3.6+

    pip install pyinstaller customtkinter Pillow requests PyYAML pycdlib

🚀 Building executable

    pyinstaller --onefile --console RetroScraper.py

# 📁 Prepare Your ROMs Folder
Organize your ROMs in a structure where each system has its own subfolder. For example:

    ROMS2/
    ├── snes/
    │   ├── Chrono Trigger.sfc
    │   └── Super Metroid.zip
    ├── psx/
    │   ├── Final Fantasy VII (Disc 1).chd
    │   └── Metal Gear Solid.cue
    └── ...

- Then run the Application
- Click the Browse button and select your main ROMs folder (e.g., ROMS2) or a console folder (e.g., snes).
- Click Start Scan.
- The application will begin processing each system folder. You can watch the progress in the log window.

# 🤝 Contributing

Contributions are welcome! If you have ideas for new features, find a bug, or want to improve the code, please feel free to open an issue or submit a pull request.

# 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.
