import os
import re
import uuid
import urllib.parse
from datetime import datetime, timezone
import requests
from google.adk.agents import Agent

TOWNS = {
    "bletchley": (51.9939, -0.7329, "Bletchley"),
    "milton keynes": (52.0406, -0.7594, "Milton Keynes"),
    "camden": (51.5390, -0.1426, "Camden"),
    "central london": (51.5074, -0.1278, "Central London"),
    "watford": (51.6565, -0.3903, "Watford"),
    "st albans": (51.7522, -0.3397, "St Albans"),
    "hemel hempstead": (51.7524, -0.4735, "Hemel Hempstead"),
    "luton": (51.8787, -0.4200, "Luton"),
    "leighton buzzard": (51.9165, -0.6617, "Leighton Buzzard"),
    "berkhamsted": (51.7602, -0.5607, "Berkhamsted"),
    "aylesbury": (51.8156, -0.8126, "Aylesbury"),
    "harrow": (51.5806, -0.3420, "Harrow"),
    "wembley": (51.5560, -0.2796, "Wembley"),
    
    # Existing entries (popular UK/London regions)
    "hornsey": (51.5872, -0.1132, "Hornsey"),
    "chafford hundred": (51.4883, 0.2952, "Chafford Hundred"),
    "barking": (51.5370, 0.0820, "Barking"),
    "stratford": (51.5417, -0.0039, "Stratford"),
    "romford": (51.5768, 0.1801, "Romford"),
    "croydon": (51.3762, -0.0982, "Croydon"),
    "richmond": (51.4613, -0.3018, "Richmond"),
    "greenwich": (51.4826, 0.0077, "Greenwich"),
    "islington": (51.5416, -0.1022, "Islington"),
    "hackney": (51.5450, -0.0553, "Hackney"),
    "chelsea": (51.4875, -0.1682, "Chelsea"),
    "ealing": (51.5130, -0.3080, "Ealing"),
    "hampstead": (51.5543, -0.1772, "Hampstead"),
    "enfield": (51.6522, -0.0808, "Enfield"),
    "barnet": (51.6531, -0.1983, "Barnet"),
    "staines": (51.4316, -0.5132, "Staines"),
    "uxbridge": (51.5456, -0.4772, "Uxbridge"),
    "slough": (51.5085, -0.5941, "Slough"),
    "maidenhead": (51.5217, -0.7177, "Maidenhead"),
    "reading": (51.4543, -0.9722, "Reading"),
    "oxford": (51.7520, -1.2577, "Oxford"),
    "grays": (51.4775, 0.3292, "Grays"),
    "east ham": (51.5348, 0.0558, "East Ham")
}

def find_midpoint_venues(locations: list[str], venue_type: str = "cafe") -> dict[str, str]:
    """Finds the snapped midpoint town and generates a Google Maps search URL.

    Args:
        locations: A list of addresses or city names, e.g. ["Bletchley", "Watford"].
        venue_type: The type of venue to search for, e.g. "cafe", "restaurant", "park".

    Returns:
        A dictionary containing:
        - "town": The snapped town name.
        - "google_maps_url": The Google Maps search URL.
    """
    headers = {"User-Agent": "MeetpointAgent/1.0 (saraschandra.kakumanu@gmail.com)"}
    coords = []
    
    # 1. Geocode each location
    for loc in locations:
        norm = loc.strip().lower()
        found = False
        if norm in TOWNS:
            coords.append(TOWNS[norm])
            found = True
        else:
            for key, val in TOWNS.items():
                if key in norm or norm in key:
                    coords.append(val)
                    found = True
                    break
        
        if not found:
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(loc)}&format=json&limit=1"
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200 and r.json():
                    data = r.json()[0]
                    coords.append((float(data["lat"]), float(data["lon"]), data.get("display_name", loc)))
            except Exception:
                pass
            
    if not coords:
        return {
            "town": "Unknown",
            "google_maps_url": "Could not geocode any of the locations."
        }
        
    # 2. Calculate average (midpoint)
    avg_lat = sum(c[0] for c in coords) / len(coords)
    avg_lon = sum(c[1] for c in coords) / len(coords)
    
    # 3. Find nearest town in the dictionary to that midpoint
    snapped_town_name = None
    min_dist = float('inf')
    for key, (lat, lon, name) in TOWNS.items():
        dist = ((lat - avg_lat) ** 2 + (lon - avg_lon) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            snapped_town_name = name
            
    if not snapped_town_name:
        snapped_town_name = "Central London"
        
    # 4. Generate URL-encoded Google Maps URL
    query_str = f"{venue_type} in {snapped_town_name}"
    encoded_query = urllib.parse.quote_plus(query_str)
    google_maps_url = f"https://www.google.com/maps/search/{encoded_query}"
    
    return {
        "town": snapped_town_name,
        "google_maps_url": google_maps_url
    }

def create_calendar_invite(title: str, start_time: str, end_time: str, attendees: list[str], location: str) -> str:
    """Creates an ICS calendar invitation file in the workspace.

    Args:
        title: The title of the calendar event.
        start_time: The start time of the event (ISO format, e.g. "2026-07-06T19:00:00").
        end_time: The end time of the event (ISO format, e.g. "2026-07-06T20:00:00").
        attendees: List of email addresses of the attendees.
        location: The location or venue name/address of the meeting.

    Returns:
        A confirmation message containing the absolute path and link to the generated ICS file.
    """
    try:
        def to_ics_time(iso_str: str) -> str:
            cleaned = re.sub(r'[:\- ]', '', iso_str).split('.')[0]
            if 'T' not in cleaned and len(cleaned) == 14:
                cleaned = cleaned[:8] + 'T' + cleaned[8:]
            return cleaned

        dtstart = to_ics_time(start_time)
        dtend = to_ics_time(end_time)
        dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        uid = str(uuid.uuid4())
        
        attendees_str = "\\n".join(attendees)
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Meetpoint Agent//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{title}
LOCATION:{location}
DESCRIPTION:Organized by Meetpoint Agent.\\nAttendees:\\n{attendees_str}
END:VEVENT
END:VCALENDAR"""

        # Generate a safe filename
        safe_title = "".join([c if c.isalnum() else "_" for c in title])
        filename = f"{safe_title}_{uid[:8]}.ics"
        filepath = os.path.join("/Users/saras/meetpoint-agent", filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(ics_content)
            
        file_link = f"[Download Invite File](file://{filepath})"
        return f"Successfully created calendar invite file: {file_link}."
    except Exception as e:
        return f"Error creating calendar invite file: {str(e)}"

def draft_whatsapp_message(recipient_phone: str, message_body: str) -> str:
    """Drafts a WhatsApp message body and generates a click-to-chat link.

    Args:
        recipient_phone: The recipient's phone number (with country code, e.g. "+15551234567").
        message_body: The body text of the message to draft.

    Returns:
        A draft summary containing the text and a direct click-to-chat WhatsApp link.
    """
    clean_phone = re.sub(r'\D', '', recipient_phone)
    encoded_message = urllib.parse.quote(message_body)
    click_to_chat_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    return f"Drafted message:\n\n{message_body}\n\n👉 [Send via WhatsApp]({click_to_chat_url})"

root_agent = Agent(
    name="meetpoint_agent",
    model="gemini-2.5-flash",
    description="Meetpoint root agent.",
    instruction="""You are a helpful meeting coordinator assistant.
When asked to find a meeting spot or midpoint between locations:
1. Call find_midpoint_venues with the locations and requested venue type.
2. The tool will return the snapped town name (e.g. 'St Albans') and a Google Maps URL of the form 'https://www.google.com/maps/search/venue_type+in+town_name'.
3. Present the snapped town to the user as the suggested meeting area, for example: 'St Albans is roughly halfway for both of you.'
4. Show the Google Maps search URL so the user can browse options there. Never search or suggest by raw coordinates.""",
    tools=[find_midpoint_venues, create_calendar_invite, draft_whatsapp_message]
)
