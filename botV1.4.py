import discord
from discord import app_commands
from openai import OpenAI
from datetime import datetime, timezone, timedelta
import pandas as pd
import re
import os
import sys
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Load environment variables from current directory
env_path = project_root / '.env'
load_dotenv(env_path)

# Enable intents
intents = discord.Intents.default()
intents.message_content = True

# Get environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not DISCORD_BOT_TOKEN or not OPENAI_API_KEY or not YOUTUBE_API_KEY:
    raise ValueError("One or more API keys are missing. Ensure they are set in the .env file.")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize APIs with correct paths
SERVICE_ACCOUNT_FILE = project_root / 'data' / 'Config' / 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Initialize APIs
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
credentials = Credentials.from_service_account_file(str(SERVICE_ACCOUNT_FILE), scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)
docs_service = build('docs', 'v1', credentials=credentials)

# Create bot instance
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)  # Initialize the command tree

    async def setup_hook(self):
        print("Setting up commands...")
        try:
            # Sync commands globally
            commands = await self.tree.sync()
            print(f"Synced {len(commands)} global commands. Registered commands:")
            for command in commands:
                print(f"- {command.name}: {command.description}")
        except Exception as e:
            print(f"Error during setup: {e}")

client = MyClient(intents=intents)

# Notify when the bot is online
@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")
    try:
        commands = await client.tree.fetch_commands()
        print("Registered commands globally:")
        for command in commands:
            print(f"- {command.name}: {command.description}")
    except Exception as e:
        print(f"Error fetching commands: {e}")

# Function to fetch video details and categorize by duration asynchronously
async def get_video_details(video_url):
    video_id = video_url.split("v=")[-1].split("&")[0] if "youtube.com" in video_url else video_url.split("/")[-1]
    print(f"Fetching details for video ID: {video_id}")

    try:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response = await asyncio.to_thread(request.execute)

        if response["items"]:
            snippet = response["items"][0]["snippet"]
            content_details = response["items"][0]["contentDetails"]
            statistics = response["items"][0].get("statistics", {})
            view_count = statistics.get("viewCount", "0")
            title = snippet["title"]
            published_at = snippet["publishedAt"]
            channel_name = snippet["channelTitle"]
            description = snippet["description"]
            # Tags might not exist for all videos
            tags = snippet.get("tags", [])
            tags_string = ", ".join(tags) if tags else ""
            duration = content_details["duration"]
            
            # Convert duration to seconds
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            seconds = int(match.group(3)) if match.group(3) else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            # Categorize video
            category = "Short" if total_seconds <= 180 else "Long-form"
            category_id = snippet.get("categoryId", "")
            
            published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            return channel_name, title, published_date.strftime("%Y-%m-%d"), category, description, tags_string, view_count, category_id, duration
    except Exception as e:
        print(f"Error fetching video details: {e}")

    return None, None, None, None, None, None, None, None, None

# Function to load banned tags
def load_banned_tags():
    try:
        with open('banned_tags.txt', 'r', encoding='utf-8') as file:
            return {tag.strip().lower() for tag in file if tag.strip()}
    except FileNotFoundError:
        print("Warning: banned_tags.txt not found. No tags will be filtered.")
        return set()

# Function to create and upload Google Sheets
def upload_to_google_sheets(data):
    # Create spreadsheet with two sheets
    spreadsheet = sheets_service.spreadsheets().create(
        body={
            'properties': {'title': 'Competition Videos'},
            'sheets': [
                {'properties': {'title': 'Videos'}},
                {'properties': {'title': 'Tag Statistics'}}
            ]
        },
    ).execute()
    
    spreadsheet_id = spreadsheet['spreadsheetId']
    videos_sheet_id = spreadsheet['sheets'][0]['properties']['sheetId']
    tags_sheet_id = spreadsheet['sheets'][1]['properties']['sheetId']

    # Upload main video data (unchanged)
    video_rows = [["Channel Name", "Date of Publishing", "Hour (GMT+2)", "Title", "Description", "Tags", "Link", "Category", "Wyświetlenia", "CategoryId", "Duration"]] + [
        [row["Channel Name"], row["Date of Publishing"], row["Hour (GMT+2)"], 
         row["Title"], row["Description"], row["Tags"], row["Link"], row["Category"], row["Wyświetlenia"], row["CategoryId"], row["Duration"]]
        for row in data
    ]

    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Videos!A1",
        valueInputOption="RAW",
        body={"values": video_rows}
    ).execute()

    # Load banned tags
    banned_tags = load_banned_tags()

    # Calculate statistics
    num_videos = len(data)
    unique_channels = len(set(item["Channel Name"] for item in data))
    
    # Get time frame
    all_times = [datetime.strptime(f"{item['Date of Publishing']} {item['Hour (GMT+2)']}", "%Y-%m-%d %H:%M") 
                 for item in data]
    earliest_time = min(all_times)
    latest_time = max(all_times)
    time_frame = f"From {earliest_time.strftime('%Y-%m-%d %H:%M')} to {latest_time.strftime('%Y-%m-%d %H:%M')} (GMT+2)"

    # Calculate tag statistics
    tag_counts = {}
    for item in data:
        if item["Tags"]:
            video_tags = [tag.strip() for tag in item["Tags"].split(',')]
            for tag in video_tags:
                # Skip empty tags and banned tags (case insensitive comparison)
                if tag and tag.lower() not in banned_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Sort tags by count
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Get top 10 tags for the chart
    top_10_tags = sorted_tags[:10] if len(sorted_tags) >= 10 else sorted_tags
    
    # Prepare tag statistics sheet content with general statistics at the top
    tag_rows = [
        ["General Statistics", ""],
        ["Number of Videos", num_videos],
        ["Time Frame", time_frame],
        ["Lookback Hours", data[0].get("Lookback Hours", "N/A")],
        ["Number of Unique Channels", unique_channels],
        ["", ""],  # Empty row for spacing
        ["Tag Statistics", ""],
        ["Tag", "Number of Uses"]
    ] + [[tag, count] for tag, count in sorted_tags]

    # Upload tag statistics
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Tag Statistics!A1",
        valueInputOption="RAW",
        body={"values": tag_rows}
    ).execute()

    # Add chart
    chart_requests = {
        "requests": [
            {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "Top 10 Most Used Tags",
                            "basicChart": {
                                "chartType": "BAR",
                                "legendPosition": "NO_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": "Number of Uses"
                                    },
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": "Tags"
                                    }
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": tags_sheet_id,
                                                        "startRowIndex": 7,  # Start after headers
                                                        "endRowIndex": 17,   # Top 10 tags
                                                        "startColumnIndex": 0,
                                                        "endColumnIndex": 1
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ],
                                "series": [
                                    {
                                        "series": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": tags_sheet_id,
                                                        "startRowIndex": 7,  # Start after headers
                                                        "endRowIndex": 17,   # Top 10 tags
                                                        "startColumnIndex": 1,
                                                        "endColumnIndex": 2
                                                    }
                                                ]
                                            }
                                        },
                                        "targetAxis": "BOTTOM_AXIS"
                                    }
                                ],
                                "headerCount": 1
                            }
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": tags_sheet_id,
                                    "rowIndex": 5,  # Moved 5 cells lower
                                    "columnIndex": 3
                                },
                                "offsetXPixels": 10,
                                "offsetYPixels": 10,
                                "widthPixels": 600,
                                "heightPixels": 400
                            }
                        }
                    }
                }
            }
        ]
    }

    # Add the chart to the sheet
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=chart_requests
    ).execute()

    # Adjust formatting (existing column width adjustments remain the same)
    requests = [
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": videos_sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 4,  # Description column
                    "endIndex": 5
                },
                "properties": {
                    "pixelSize": 400
                },
                "fields": "pixelSize"
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": videos_sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 5,  # Tags column
                    "endIndex": 6
                },
                "properties": {
                    "pixelSize": 300
                },
                "fields": "pixelSize"
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": tags_sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,  # Tag column
                    "endIndex": 1
                },
                "properties": {
                    "pixelSize": 300
                },
                "fields": "pixelSize"
            }
        }
    ]
    
    # Add formatting for headers and statistics
    requests.extend([
        {
            "repeatCell": {
                "range": {
                    "sheetId": tags_sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                        "textFormat": {"bold": True, "fontSize": 12}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": tags_sheet_id,
                    "startRowIndex": 6,
                    "endRowIndex": 8
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                        "textFormat": {"bold": True}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        }
    ])

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()

    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body={"role": "writer", "type": "anyone"},
    ).execute()

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

# Function to create and upload a Google Docs file with the AI analysis
def upload_to_google_docs(analysis_text):
    try:
        # Create a new Google Docs file
        doc = drive_service.files().create(
            body={
                'name': 'YouTube Analysis Report',
                'mimeType': 'application/vnd.google-apps.document'
            },
            fields='id'
        ).execute()
        
        doc_id = doc.get('id')

        # Use Google Docs API to write content into the document
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': analysis_text
                }
            }
        ]
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

        # Make the document public
        drive_service.permissions().create(
            fileId=doc_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        return f"https://docs.google.com/document/d/{doc_id}/edit"

    except Exception as e:
        print(f"Error creating Google Docs file: {e}")
        return None

# Slash command to generate a Google Sheet and Google Docs analysis
@client.tree.command(name="generate_sheet", description="Generate a Google Sheet from messages")
async def generate_sheet(interaction: discord.Interaction, lookback_hours: int):
    await interaction.response.defer(ephemeral=True)
    
    now = datetime.now(timezone.utc)
    lookback_time = now - timedelta(hours=lookback_hours)
    data = []
    pattern = r"(https://(?:www\.youtube\.com/watch\?v=|youtu\.be/)\S+)"

    async for message in interaction.channel.history(limit=1000):
        if message.created_at < lookback_time:
            continue
        
        match = re.search(pattern, message.content)
        if match:
            video_link = match.group(1).strip()
            channel_name, title, published_date, category, description, tags, view_count, category_id, duration = await get_video_details(video_link)
            if channel_name and title:
                time_posted = message.created_at.astimezone(timezone(timedelta(hours=2)))
                data.append({
                    "Channel Name": channel_name,
                    "Date of Publishing": published_date,
                    "Hour (GMT+2)": time_posted.strftime("%H:%M"),
                    "Title": title,
                    "Description": description,
                    "Tags": tags,
                    "Link": video_link,
                    "Category": category,
                    "Wyświetlenia": view_count, # Add view count to the data
                    "CategoryId": category_id,
                    "Duration": duration,
                    "Lookback Hours": lookback_hours  # Add lookback hours to the data
                })

    if data:
        sheet_link = upload_to_google_sheets(data)
        await interaction.followup.send(f"Here is your Google Sheets file: {sheet_link}", ephemeral=True)
    else:
        await interaction.followup.send("No relevant messages found.", ephemeral=True)

# Run the bot
client.run(DISCORD_BOT_TOKEN)
