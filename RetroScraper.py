import os
import xml.etree.ElementTree as ET
import requests
import shutil
import re
from pathlib import Path
from difflib import SequenceMatcher
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import threading
import logging
from datetime import datetime
from xml.dom import minidom
import zipfile
import io

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Platform mapping dictionary
PLATFORM_MAPPING = {
    "dreamcast": "Sega Dreamcast",
    "snes": "Super Nintendo Entertainment System",
    "nes": "Nintendo Entertainment System",
    "gb": "Nintendo Game Boy",
    "gbc": "Nintendo Game Boy Color",
    "psx": "Sony Playstation",
    "psp": "Sony PSP",
    "n64": "Nintendo 64",
    "nds": "Nintendo DS",
    "gba": "Game Boy Advance",
    "ps2": "PlayStation 2",
    "gc": "Nintendo GameCube",
    "arcade": "Arcade",
    "naomi ": "Arcade",
    "cps1": "Arcade",
    "cps2": "Arcade",
    "cps3": "Arcade",
    "megadrive": "Sega Genesis",
    "genesis": "Sega Genesis",
    "saturn": "Sega Saturn",
    "mastersystem ": "Sega Master System",
    # Add more mappings as needed
}

# File extensions to scan
SCAN_EXTENSIONS = {'.zip', '.sfc', '.smc', '.sgd', '.smd', '.sms', '.nes', '.gb', '.gbc', '.iso', '.cue', '.chd', '.gba', '.n64', '.nds', '.rvz'}

class GameOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("RetroScraper")
        self.geometry("900x700")
        
        # Variables
        self.scan_folder = ctk.StringVar()
        self.scanning = False
        self.progress_value = ctk.DoubleVar(value=0)
        self.status_text = ctk.StringVar(value="Ready to scan")
        self.platform_status = ctk.StringVar(value="No platform being scanned")
        
        # Setup logging
        self.setup_logging()
        
        # Create UI
        self.create_widgets()
        
        # Set metadata path
        self.metadata_path = Path(__file__).parent / "Metadata.xml"
        
    def setup_logging(self):
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create log file with timestamp
        log_file = log_dir / f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Application started")
    
    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="RetroScraper", 
                                  font=ctk.CTkFont(family="Small Fonts", size=46, weight="bold"))
        title_label.pack(pady=20)
        
        # Scan folder selection
        scan_frame = ctk.CTkFrame(main_frame)
        scan_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(scan_frame, text="Games Folder:").pack(anchor="w", padx=10, pady=(10, 5))
        
        folder_frame = ctk.CTkFrame(scan_frame, fg_color="transparent")
        folder_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkEntry(folder_frame, textvariable=self.scan_folder).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(folder_frame, text="Browse", width=100, 
                     command=self.browse_scan_folder).pack(side="right")
        
        # Platform status
        platform_frame = ctk.CTkFrame(main_frame)
        platform_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(platform_frame, text="Current Platform:").pack(anchor="w", padx=10, pady=(10, 5))
        
        self.platform_status_label = ctk.CTkLabel(platform_frame, textvariable=self.platform_status)
        self.platform_status_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Progress bar
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(progress_frame, textvariable=self.status_text).pack(anchor="w", padx=10, pady=(10, 5))
        ctk.CTkProgressBar(progress_frame, variable=self.progress_value).pack(fill="x", padx=10, pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Start Scan", command=self.start_scan, 
                     width=120, height=40).pack(side="left", padx=20)
        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel_scan, 
                     width=120, height=40, fg_color="red", hover_color="darkred").pack(side="right", padx=20)
        
        # Log area
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(log_frame, text="Activity Log:").pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(log_frame)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def check_metadata(self):
        """Check if metadata file exists, download if needed"""
        if self.metadata_path.exists():
            self.log("Metadata.xml found")
            self.logger.info("Metadata.xml found")
            return True
        
        self.log("Downloading metadata...")
        self.logger.info("Metadata.xml not found, downloading...")
        
        try:
            # Download metadata zip
            url = "https://gamesdb.launchbox-app.com/Metadata.zip"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Extract only Metadata.xml
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                with zip_file.open("Metadata.xml") as source, open(self.metadata_path, "wb") as target:
                    shutil.copyfileobj(source, target)
            
            self.log("Metadata.xml downloaded successfully")
            self.logger.info("Metadata.xml downloaded successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to download metadata: {str(e)}"
            self.log(error_msg)
            self.logger.error(error_msg)
            return False
    
    def browse_scan_folder(self):
        folder = filedialog.askdirectory(title="Select Games Folder")
        if folder:
            self.scan_folder.set(folder)
            self.logger.info(f"Selected games folder: {folder}")
    
    def start_scan(self):
        if not self.scan_folder.get():
            messagebox.showerror("Error", "Please select a games folder to scan")
            return
        
        # Check for metadata file
        if not self.check_metadata():
            messagebox.showerror("Error", "Metadata file not found and could not be downloaded")
            return
        
        self.scanning = True
        self.progress_value.set(0)
        self.status_text.set("Scanning...")
        self.platform_status.set("No platform being scanned")
        self.log_text.delete("1.0", "end")
        self.log("Starting scan...")
        
        # Run scan in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.run_scan)
        thread.daemon = True
        thread.start()
    
    def cancel_scan(self):
        self.scanning = False
        self.status_text.set("Scan cancelled")
        self.platform_status.set("Scan cancelled")
        self.log("Scan was cancelled by user")
        self.logger.warning("Scan cancelled by user")
    
    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.update_idletasks()
    
    def run_scan(self):
        try:
            # Load metadata
            self.log("Loading metadata file...")
            self.logger.info("Loading metadata file")
            metadata_tree = ET.parse(self.metadata_path)
            metadata_root = metadata_tree.getroot()
            
            # Find all game files
            self.log("Scanning for game files...")
            self.logger.info("Scanning for game files")
            
            scan_path = Path(self.scan_folder.get())
            
            # Check if the selected folder is a platform folder itself
            platform_name = scan_path.name.lower()
            if platform_name in PLATFORM_MAPPING:
                # User selected a platform folder directly
                self.log(f"Scanning platform folder directly: {platform_name}")
                self.logger.info(f"Scanning platform folder directly: {platform_name}")
                
                # Process this single platform folder
                games_by_platform = {}
                games = []
                
                for file in scan_path.iterdir():
                    if file.is_file() and file.suffix.lower() in SCAN_EXTENSIONS:
                        games.append(file)
                
                if games:
                    games_by_platform[scan_path] = games
                else:
                    self.log("No game files found in the selected platform folder")
                    self.logger.warning("No game files found in the selected platform folder")
            else:
                # User selected a folder containing platform subfolders
                self.log("Scanning for platform subfolders...")
                self.logger.info("Scanning for platform subfolders")
                
                game_files = []
                platforms_found = set()
                
                for platform_folder in scan_path.iterdir():
                    if platform_folder.is_dir():
                        platform_name = platform_folder.name.lower()
                        if platform_name in PLATFORM_MAPPING:
                            platforms_found.add(platform_name)
                            for file in platform_folder.iterdir():
                                if file.is_file() and file.suffix.lower() in SCAN_EXTENSIONS:
                                    game_files.append((platform_folder, file))
                                    self.logger.debug(f"Found game file: {file.name} in {platform_name}")
                
                # Group games by platform folder
                games_by_platform = {}
                for platform_folder, game_file in game_files:
                    if platform_folder not in games_by_platform:
                        games_by_platform[platform_folder] = []
                    games_by_platform[platform_folder].append(game_file)
            
            if not games_by_platform:
                self.log("No platform folders or game files found")
                self.logger.warning("No platform folders or game files found")
                self.status_text.set("No platforms found")
                return
            
            self.log(f"Found {sum(len(games) for games in games_by_platform.values())} game files across {len(games_by_platform)} platforms")
            self.logger.info(f"Found {sum(len(games) for games in games_by_platform.values())} game files across {len(games_by_platform)} platforms")
            
            # Process each platform folder
            processed_platforms = 0
            total_platforms = len(games_by_platform)
            
            for platform_folder, games in games_by_platform.items():
                if not self.scanning:
                    break
                
                platform_name = platform_folder.name.lower()
                platform_display_name = PLATFORM_MAPPING.get(platform_name, platform_name)
                self.platform_status.set(f"Scanning: {platform_display_name}")
                self.process_platform(platform_folder, games, metadata_root)
                processed_platforms += 1
                self.progress_value.set(processed_platforms / total_platforms)
                self.status_text.set(f"Processing platforms... ({processed_platforms}/{total_platforms})")
            
            if self.scanning:
                self.status_text.set("Scan completed successfully")
                self.platform_status.set("Scan completed")
                self.log("Scan completed successfully")
                self.logger.info("Scan completed successfully")
                messagebox.showinfo("Success", "Scan completed successfully")
            else:
                self.log("Scan was cancelled")
                self.logger.warning("Scan was cancelled")
                
        except Exception as e:
            error_msg = f"Error during scan: {str(e)}"
            self.log(error_msg)
            self.status_text.set("Error occurred")
            self.platform_status.set("Error occurred")
            self.logger.exception("Error during scan")
            messagebox.showerror("Error", f"An error occurred during scanning: {str(e)}")
        
        self.scanning = False
    
    def process_platform(self, platform_folder, games, metadata_root):
        """Process all games in a platform folder and update gamelist.xml once"""
        platform_name = platform_folder.name.lower()
        metadata_platform = PLATFORM_MAPPING.get(platform_name, "")
        
        if not metadata_platform:
            msg = f"Skipping platform {platform_name}: No platform mapping found"
            self.log(msg)
            self.logger.warning(msg)
            return
        
        # Load or create exclusion list
        exclusion_file = platform_folder / "Excluded_From_Scan.txt"
        excluded_files = self.load_exclusion_list(exclusion_file)
        
        # Load or create gamelist.xml
        gamelist_path = platform_folder / "gamelist.xml"
        backup_created = False
        
        if gamelist_path.exists():
            try:
                # Create backup only once per platform
                backup_path = platform_folder / "gamelist.xml.bak"
                if not backup_path.exists():
                    shutil.copy2(gamelist_path, backup_path)
                    backup_created = True
                    self.logger.info(f"Created backup of gamelist.xml: {backup_path}")
                
                # Parse existing gamelist
                tree = ET.parse(gamelist_path)
                root = tree.getroot()
                
                # Remove XML declaration if it exists in the content
                content = gamelist_path.read_text(encoding='utf-8')
                if content.startswith('<?xml'):
                    # Find the end of the XML declaration
                    end_decl = content.find('?>') + 2
                    content = content[end_decl:].lstrip()
                
                # Re-parse the content without the declaration
                root = ET.fromstring(content)
                
            except ET.ParseError as e:
                msg = f"Error parsing {gamelist_path}: {str(e)}. Creating a new one."
                self.log(msg)
                self.logger.warning(msg)
                # If the XML is invalid, create a new root
                root = ET.Element("gameList")
        else:
            # Create new gamelist
            root = ET.Element("gameList")
            self.logger.info(f"Creating new gamelist.xml at {gamelist_path}")
        
        # Process each game in the platform folder
        processed_games = 0
        total_games = len(games)
        
        for game_file in games:
            if not self.scanning:
                break
                
            # Check if file is in exclusion list
            if game_file.name in excluded_files:
                msg = f"Skipping {game_file.name}: File is in exclusion list"
                self.log(msg)
                self.logger.info(msg)
                continue
                
            processed = self.process_game(platform_folder, game_file, metadata_root, metadata_platform, root, exclusion_file, excluded_files)
            if processed:
                processed_games += 1
                
            self.log(f"Processed {processed_games}/{total_games} games in {platform_name}")
        
        # Only write to file if we found new games to add
        if processed_games > 0:
            # Write to file with proper formatting
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="\t")
            
            # Remove extra lines added by minidom and the XML declaration
            lines = pretty_xml.split('\n')
            # Skip the first line (XML declaration) and any empty lines
            lines = [line for line in lines[1:] if line.strip()]
            
            with open(gamelist_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0"?>\n')
                for line in lines:
                    f.write(line + '\n')
            
            self.logger.info(f"Updated gamelist.xml for {platform_name} with {processed_games} new games")
            self.log(f"Updated gamelist.xml for {platform_name} with {processed_games} new games")
    
    def load_exclusion_list(self, exclusion_file):
        """Load the list of excluded files from the exclusion file"""
        excluded_files = set()
        
        if exclusion_file.exists():
            try:
                with open(exclusion_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        filename = line.strip()
                        if filename:  # Skip empty lines
                            excluded_files.add(filename)
                self.logger.info(f"Loaded {len(excluded_files)} files from exclusion list: {exclusion_file}")
            except Exception as e:
                self.logger.error(f"Error reading exclusion file {exclusion_file}: {str(e)}")
        
        return excluded_files
    
    def add_to_exclusion_list(self, exclusion_file, filename):
        """Add a filename to the exclusion list"""
        try:
            with open(exclusion_file, 'a', encoding='utf-8') as f:
                f.write(f"{filename}\n")
            self.logger.info(f"Added {filename} to exclusion list: {exclusion_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding {filename} to exclusion file {exclusion_file}: {str(e)}")
            return False
    
    def process_game(self, platform_folder, game_file, metadata_root, metadata_platform, root, exclusion_file, excluded_files):
        """Process a single game and add it to the XML root if not already present"""
        # Check if game already exists in the XML
        for game_elem in root.findall("game"):
            path_elem = game_elem.find("path")
            if path_elem is not None and path_elem.text == f"./{game_file.name}":
                msg = f"Skipping {game_file.name}: Already exists in gamelist.xml"
                self.log(msg)
                self.logger.info(msg)
                return False
        
        # Find matching game in metadata
        game_name_no_ext = self.clean_game_name(game_file.stem)
        best_match = None
        best_score = 0
        exact_match = False
        
        for game_elem in metadata_root.findall("Game"):
            name_elem = game_elem.find("Name")
            platform_elem = game_elem.find("Platform")
            
            if (name_elem is not None and name_elem.text and 
                platform_elem is not None and platform_elem.text == metadata_platform):
                
                metadata_name = self.clean_game_name(name_elem.text)
                
                # First try exact match
                if game_name_no_ext.lower() == metadata_name.lower():
                    best_match = game_elem
                    exact_match = True
                    break
                
                # Calculate similarity score if no exact match
                score = self.similarity(game_name_no_ext.lower(), metadata_name.lower())
                if score > best_score and score > 0.7:  # Higher threshold for matching
                    best_score = score
                    best_match = game_elem
        
        if best_match is None:
            msg = f"No metadata found for {game_file.name} (cleaned: {game_name_no_ext}) on platform {metadata_platform}"
            self.log(msg)
            self.logger.info(msg)
            
            # Add to exclusion list
            if game_file.name not in excluded_files:
                if self.add_to_exclusion_list(exclusion_file, game_file.name):
                    excluded_files.add(game_file.name)
                    self.log(f"Added {game_file.name} to exclusion list")
            
            return False
        
        match_type = "exact" if exact_match else f"fuzzy (score: {best_score:.2f})"
        msg = f"Processing {game_file.name} -> {best_match.find('Name').text} ({match_type})"
        self.log(msg)
        self.logger.info(msg)
        
        # Add game to XML
        self.add_game_to_xml(root, game_file, best_match)
        
        # Download images
        self.download_images(platform_folder, game_file, best_match, metadata_root)
        
        return True
    
    def clean_game_name(self, name):
        # Remove common tags and formatting from game names
        patterns = [
            r'\([^)]*\)',  # Remove anything in parentheses
            r'\[[^\]]*\]',  # Remove anything in brackets
            r'\.',          # Remove dots
            r'\-',          # Remove hyphens
            r'\_',          # Remove underscores
            r'\s+',         # Replace multiple spaces with single space
        ]
        
        cleaned = name
        for pattern in patterns:
            cleaned = re.sub(pattern, ' ', cleaned)
        
        # Remove common words that might differ between filename and metadata
        common_words = ['usa', 'europe', 'japan', 'english', 'rev', 'version', 'disk', 'disc']
        words = cleaned.split()
        filtered_words = [word for word in words if word.lower() not in common_words]
        
        return ' '.join(filtered_words).strip()
    
    def similarity(self, a, b):
        return SequenceMatcher(None, a, b).ratio()
    
    def add_game_to_xml(self, root, game_file, game_elem):
        # Create game element
        game = ET.SubElement(root, "game")
        
        # Add path
        path_elem = ET.SubElement(game, "path")
        path_elem.text = f"./{game_file.name}"
        
        # Add name
        name_elem = ET.SubElement(game, "name")
        name_text = game_elem.find("Name").text if game_elem.find("Name") is not None else ""
        name_elem.text = name_text
        
        # Add description
        desc_elem = ET.SubElement(game, "desc")
        overview_elem = game_elem.find("Overview")
        desc_text = overview_elem.text if overview_elem is not None else ""
        # Clean up description text
        desc_text = re.sub(r'\s+', ' ', desc_text).strip()
        desc_elem.text = desc_text
        
        # Add image paths
        image_base = f"./images/{game_file.stem}"
        ET.SubElement(game, "image").text = f"{image_base}-image.png"
        ET.SubElement(game, "marquee").text = f"{image_base}-marquee.png"
        ET.SubElement(game, "thumbnail").text = f"{image_base}-thumbnail.png"
        
        # Add rating (convert from 0-5 scale to 0-1 scale)
        rating_elem = ET.SubElement(game, "rating")
        community_rating = game_elem.find("CommunityRating")
        if community_rating is not None and community_rating.text:
            try:
                # Convert from 0-5 scale to 0-1 scale
                rating = float(community_rating.text) / 5.0
                rating_elem.text = f"{rating:.2f}"[:4]  # Format to 2 decimal places
            except ValueError:
                rating_elem.text = "0.00"
                self.logger.warning(f"Invalid rating value: {community_rating.text}")
        else:
            rating_elem.text = "0.00"
        
        # Add release date
        release_elem = ET.SubElement(game, "releasedate")
        release_date = game_elem.find("ReleaseDate")
        if release_date is not None and release_date.text:
            # Extract date part only (YYYY-MM-DD)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', release_date.text)
            if date_match:
                date_str = date_match.group(1).replace("-", "")
                release_elem.text = date_str + "T000000"
            else:
                self.logger.warning(f"Could not parse release date: {release_date.text}")
                release_elem.text = ""
        else:
            release_elem.text = ""
        
        # Add developer
        developer_elem = ET.SubElement(game, "developer")
        developer = game_elem.find("Developer")
        developer_elem.text = developer.text if developer is not None else ""
        
        # Add publisher
        publisher_elem = ET.SubElement(game, "publisher")
        publisher = game_elem.find("Publisher")
        publisher_elem.text = publisher.text if publisher is not None else ""
        
        # Add genre
        genre_elem = ET.SubElement(game, "genre")
        genres = game_elem.find("Genres")
        genre_elem.text = genres.text if genres is not None else ""
        
        # Add players
        players_elem = ET.SubElement(game, "players")
        max_players = game_elem.find("MaxPlayers")
        if max_players is not None and max_players.text:
            min_players = game_elem.find("MinPlayers")
            min_text = min_players.text if min_players is not None else "1"
            players_elem.text = f"{min_text}-{max_players.text}"
        else:
            players_elem.text = "1-1"
    
    def download_images(self, platform_folder, game_file, game_elem, metadata_root):
        # Create images directory if it doesn't exist
        images_dir = platform_folder / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Get database ID
        db_id_elem = game_elem.find("DatabaseID")
        if db_id_elem is None:
            self.logger.warning(f"No DatabaseID found for {game_file.name}")
            return
        
        db_id = db_id_elem.text
        
        # Find image elements in metadata
        image_types = [
            ("Screenshot - Gameplay", "image"),
            ("Clear Logo", "marquee"),
            ("Box - Front", "thumbnail")
        ]
        
        for image_type, suffix in image_types:
            # Find the image entry in metadata
            image_info = None
            
            # For screenshots, if the exact type isn't found, look for any type containing "Screenshot"
            if image_type == "Screenshot - Gameplay":
                # First try exact match
                for game_image in metadata_root.findall(".//GameImage"):
                    type_elem = game_image.find("Type")
                    db_id_elem_img = game_image.find("DatabaseID")
                    
                    if (type_elem is not None and type_elem.text == image_type and
                        db_id_elem_img is not None and db_id_elem_img.text == db_id):
                        
                        file_name_elem = game_image.find("FileName")
                        if file_name_elem is not None and file_name_elem.text:
                            image_info = file_name_elem.text
                            break
                
                # If exact match not found, look for any screenshot
                if image_info is None:
                    for game_image in metadata_root.findall(".//GameImage"):
                        type_elem = game_image.find("Type")
                        db_id_elem_img = game_image.find("DatabaseID")
                        
                        if (type_elem is not None and "Screenshot" in type_elem.text and
                            db_id_elem_img is not None and db_id_elem_img.text == db_id):
                            
                            file_name_elem = game_image.find("FileName")
                            if file_name_elem is not None and file_name_elem.text:
                                image_info = file_name_elem.text
                                self.log(f"  Using alternative screenshot: {type_elem.text}")
                                self.logger.info(f"Using alternative screenshot for {game_file.name}: {type_elem.text}")
                                break
            else:
                # For other image types, use exact match
                for game_image in metadata_root.findall(".//GameImage"):
                    type_elem = game_image.find("Type")
                    db_id_elem_img = game_image.find("DatabaseID")
                    
                    if (type_elem is not None and type_elem.text == image_type and
                        db_id_elem_img is not None and db_id_elem_img.text == db_id):
                        
                        file_name_elem = game_image.find("FileName")
                        if file_name_elem is not None and file_name_elem.text:
                            image_info = file_name_elem.text
                            break
            
            if image_info:
                # Download image
                url = f"https://images.launchbox-app.com/{image_info}"
                image_path = images_dir / f"{game_file.stem}-{suffix}.png"
                
                try:
                    # Check if image already exists
                    if image_path.exists():
                        self.logger.info(f"Image already exists: {image_path}")
                        continue
                    
                    self.logger.info(f"Downloading {suffix} image from: {url}")
                    response = requests.get(url, stream=True, timeout=30)
                    if response.status_code == 200:
                        with open(image_path, 'wb') as out_file:
                            response.raw.decode_content = True
                            shutil.copyfileobj(response.raw, out_file)
                        
                        # Resize marquee images if they are wider than 400px
                        if suffix == "marquee":
                            self.resize_marquee_image(image_path)
                        
                        self.log(f"  Downloaded {suffix} image")
                        self.logger.info(f"Downloaded {suffix} image to: {image_path}")
                    else:
                        msg = f"Failed to download {suffix} image: HTTP {response.status_code}"
                        self.log(msg)
                        self.logger.warning(msg)
                except Exception as e:
                    msg = f"Error downloading {suffix} image: {str(e)}"
                    self.log(msg)
                    self.logger.error(msg)
            else:
                self.logger.warning(f"No {image_type} image found for {game_file.name}")
    
    def resize_marquee_image(self, image_path):
        """Resize marquee image if it's wider than 400px while maintaining aspect ratio"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                if width > 400:
                    # Calculate new height while maintaining aspect ratio
                    new_width = 400
                    new_height = int((new_width / width) * height)
                    
                    # Resize the image
                    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Save the resized image
                    resized_img.save(image_path, "PNG")
                    
                    self.log(f"  Resized marquee image from {width}x{height} to {new_width}x{new_height}")
                    self.logger.info(f"Resized marquee image from {width}x{height} to {new_width}x{new_height}")
                else:
                    self.logger.info(f"Marquee image size is {width}x{height} (no resizing needed)")
                    
        except Exception as e:
            self.logger.error(f"Error resizing marquee image {image_path}: {str(e)}")

if __name__ == "__main__":
    app = GameOrganizerApp()
    app.mainloop()