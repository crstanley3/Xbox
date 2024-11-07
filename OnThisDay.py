import tkinter as tk
from PIL import Image, ImageTk
import pandas as pd
import requests
from io import BytesIO
import urllib3
from datetime import datetime
from bs4 import BeautifulSoup

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to load achievements and filter by today's date
def load_achievements():
    print("Loading achievements from CSV file...")
    file_path = r'C:\Users\crisp\Desktop\A Tracker\Achievements.csv'  # Replace with your actual CSV file path
    achievements_df = pd.read_csv(file_path)
    
    # Convert 'UnlockDate' to datetime format
    achievements_df['UnlockDate'] = pd.to_datetime(achievements_df['UnlockDate'])
    
    # Get today's date
    today = datetime.now().date()
    
    # Filter for the month and day of today's date
    achievements_df['MonthDay'] = achievements_df['UnlockDate'].dt.strftime('%m-%d')
    filtered_df = achievements_df[achievements_df['MonthDay'] == today.strftime('%m-%d')]
    
    print(f"Loaded {len(filtered_df)} achievements unlocked on {today}")  # Debugging output
    return filtered_df[['GameName', 'AchievementName', 'AchievementPageURL', 'UnlockDate']]

# Function to scrape the image URL and download the achievement and game art
def get_images(page_url, achievement_name):
    try:
        print(f"Scraping achievement page URL: {page_url}")
        response = requests.get(page_url, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Initialize storage for images
        achievement_art = None
        game_art = None

        # Locate all image tags and differentiate based on attributes
        img_tags = soup.find_all('img')
        for img in img_tags:
            img_url = "https://www.trueachievements.com" + img['src']
            alt_text = img.get('alt', '').lower()
            width = img.get('width', None)
            srcset = img.get('srcset', '')

            # Identify achievement art
            if not achievement_art and width == '48' and (achievement_name.lower() in alt_text or "achievement" in srcset or "64w" in srcset):
                print(f"Found achievement art URL: {img_url}")
                achievement_art = fetch_image(img_url)

            # Identify game art with a fallback if not initially found
            elif not game_art and (width == '48' or "game" in alt_text):
                print(f"Found game art URL: {img_url}")
                game_art = fetch_image(img_url)

            # Break early if both images are found
            if achievement_art and game_art:
                break

        if not achievement_art and not game_art:
            print("No images found")
        return game_art, achievement_art

    except Exception as e:
        print(f"Error scraping or downloading images: {e}")
        return None, None

# Helper function to fetch and process images
def fetch_image(url):
    try:
        print(f"Fetching image from {url}")
        image_response = requests.get(url, verify=False)
        if image_response.status_code == 200:
            image_data = BytesIO(image_response.content)
            image = Image.open(image_data)
            image = image.resize((64, 64), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        else:
            print(f"Failed to fetch image from {url}. HTTP status code: {image_response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None

# Function to update the widget with achievements for today's date
def update_widget():
    print("Updating the widget with achievements for today...")
    # Clear existing labels and images
    for widget in frame.winfo_children():
        widget.destroy()
    images.clear()

    # Load and filter data
    achievements = load_achievements()
    for index, row in achievements.iterrows():
        print(f"Inserting achievement: {row['AchievementName']} from game {row['GameName']}")
        game_art, achievement_art = get_images(row['AchievementPageURL'], row['AchievementName'])
        if game_art or achievement_art:
            # Create a frame to hold the images and text together
            achievement_frame = tk.Frame(frame, bg='#008000')
            achievement_frame.pack(anchor='w', pady=5)
            
            if game_art:
                images.append(game_art)
                game_art_label = tk.Label(achievement_frame, image=game_art, bg='#008000')
                game_art_label.pack(side='left', padx=5)
            
            if achievement_art:
                images.append(achievement_art)
                achievement_art_label = tk.Label(achievement_frame, image=achievement_art, bg='#008000')
                achievement_art_label.pack(side='left', padx=5)
            
            # Create a label for the text and add it to the frame
            unlock_date_str = row['UnlockDate'].strftime('%Y-%m-%d')
            text_label = tk.Label(achievement_frame, text=f"{row['GameName']}: {row['AchievementName']}\nUnlocked at: {unlock_date_str}", bg='#008000', fg='white')
            text_label.pack(side='left', padx=5)
        else:
            print(f"No images found for {row['AchievementName']}, inserting text only.")
            unlock_date_str = row['UnlockDate'].strftime('%Y-%m-%d')
            text_label = tk.Label(frame, text=f"{row['GameName']}: {row['AchievementName']}\nUnlocked at: {unlock_date_str}", bg='#008000', fg='white')
            text_label.pack(anchor='w', pady=5)
    print("Widget update completed.")

# Creating the main window
print("Initializing Tkinter window...")
root = tk.Tk()
root.title("Today's Achievements")
root.configure(bg='#008000')  # Set background color for the main window

# Creating a frame for the canvas and scrollbar
outer_frame = tk.Frame(root, bg='#008000')
outer_frame.pack(expand=True, fill='both', padx=10, pady=10)

# Create a canvas widget inside the outer frame
canvas = tk.Canvas(outer_frame, bg='#008000')
canvas.pack(side='left', fill='both', expand=True)

# Add a scrollbar to the canvas
scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
scrollbar.pack(side='right', fill='y')

# Configure the canvas to use the scrollbar
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Create a frame inside the canvas for the content
frame = tk.Frame(canvas, bg='#008000')
canvas.create_window((0, 0), window=frame, anchor='nw')

# Keep a list to store images so they aren't garbage collected
images = []

# Initial update and layout
update_widget()

# Run the application
print("Running Tkinter main loop")  # Debugging output
root.mainloop()
print("Tkinter main loop has exited.")  # This will print when the window is closed
