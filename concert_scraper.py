import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional, Tuple
import json
from urllib.parse import urljoin
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

class ArtistRecognizer:
    """
    Lightweight artist name recognizer for concert events
    No ML required – rule + pattern based (FAST & RELIABLE)
    """

    COMMON_NOISE = {
        'live', 'concert', 'tour', 'world', 'show', 'event',
        'feat', 'featuring', 'with', 'and', '&',
        'in', 'at', 'malaysia', 'kuala', 'lumpur', 'kl',
        '2024', '2025', '2026', '2027'
    }

    def extract_artist_from_title(self, title: str) -> str:
        """
        Extract likely artist name from event title
        """
        if not title:
            return ''

        original = title
        title = title.lower()

        # Remove brackets content
        title = re.sub(r'\(.*?\)|\[.*?\]', ' ', title)

        # Common separators
        parts = re.split(r'live in|world tour|tour|concert|show|:', title)

        candidate = parts[0]

        # Remove special chars
        candidate = re.sub(r'[^\w\s]', ' ', candidate)
        words = [w for w in candidate.split() if w not in self.COMMON_NOISE]

        # Heuristic: artist names usually 1–4 words
        if 1 <= len(words) <= 4:
            return ' '.join(w.title() for w in words)

        return original.title()

    def extract_artist_from_query(self, query: str) -> str:
        """
        Extract artist name from user query
        """
        if not query:
            return ''

        query = query.lower()
        query = re.sub(r'find|search|concert|tickets|show|live|in malaysia', '', query)
        query = re.sub(r'[^\w\s]', ' ', query)

        words = [w for w in query.split() if w not in self.COMMON_NOISE]

        if 1 <= len(words) <= 4:
            return ' '.join(w.title() for w in words)

        return ''

class MalaysiaConcertScraper:
    
    def __init__(self):
        self.artist_recognizer = ArtistRecognizer()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.timeout = 15
        self.max_retries = 2
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
        
        # IMPROVED: Expanded venue database with exact locations
        self.known_venues = {
            'axiata arena', 'bukit jalil', 'stadium bukit jalil',
            'zepp kl', 'zepp kuala lumpur', 'stadium merdeka',
            'klcc', 'kuala lumpur convention centre', 'sunway lagoon',
            'genting arena', 'arena of stars', 'dewan filharmonik petronas',
            'mega star arena', 'the bee publika', 'bentley music auditorium',
            'kl live', 'istana budaya', 'trec kl', 'pavilion kl',
            'mid valley', 'quill city mall', 'mytown shopping centre',
            'surf beach sunway lagoon', 'setia city convention centre',
            'spice arena', 'klpac', 'genting international showroom',
        }
        
        # IMPROVED: Venue to exact name + location mapping
        self.venue_database = {
            'axiata arena': ('Axiata Arena', 'Bukit Jalil, Kuala Lumpur'),
            'arena bukit jalil': ('Axiata Arena', 'Bukit Jalil, Kuala Lumpur'),
            'bukit jalil': ('Axiata Arena', 'Bukit Jalil, Kuala Lumpur'),
            'stadium bukit jalil': ('Bukit Jalil National Stadium', 'Bukit Jalil, Kuala Lumpur'),
            'stadium merdeka': ('Stadium Merdeka', 'Kuala Lumpur'),
            'zepp kl': ('Zepp KL', 'Kuala Lumpur'),
            'zepp kuala lumpur': ('Zepp KL', 'Kuala Lumpur'),
            'klcc': ('KLCC Convention Centre', 'Kuala Lumpur'),
            'kuala lumpur convention centre': ('KLCC Convention Centre', 'Kuala Lumpur'),
            'sunway lagoon': ('Sunway Lagoon Surf Beach', 'Sunway, Selangor'),
            'surf beach': ('Sunway Lagoon Surf Beach', 'Sunway, Selangor'),
            'surf beach sunway lagoon': ('Sunway Lagoon Surf Beach', 'Sunway, Selangor'),
            'arena of stars': ('Arena of Stars', 'Genting Highlands'),
            'genting arena': ('Arena of Stars', 'Genting Highlands'),
            'genting international showroom': ('Genting International Showroom', 'Genting Highlands'),
            'cloud 9': ('Cloud 9', 'Genting Highlands'),
            'dewan filharmonik petronas': ('Dewan Filharmonik Petronas', 'Kuala Lumpur'),
            'dewan filharmonik': ('Dewan Filharmonik Petronas', 'Kuala Lumpur'),
            'dfp': ('Dewan Filharmonik Petronas', 'Kuala Lumpur'),
            'mega star arena': ('Mega Star Arena', 'Kuala Lumpur'),
            'the bee publika': ('The Bee, Publika', 'Kuala Lumpur'),
            'the bee': ('The Bee, Publika', 'Kuala Lumpur'),
            'publika': ('The Bee, Publika', 'Kuala Lumpur'),
            'bentley music auditorium': ('Bentley Music Auditorium', 'Kuala Lumpur'),
            'bentley music': ('Bentley Music Auditorium', 'Kuala Lumpur'),
            'kl live': ('KL Live', 'Kuala Lumpur'),
            'istana budaya': ('Istana Budaya', 'Kuala Lumpur'),
            'trec kl': ('TREC KL', 'Kuala Lumpur'),
            'pavilion kl': ('Pavilion KL', 'Kuala Lumpur'),
            'pavilion': ('Pavilion KL', 'Kuala Lumpur'),
            'mid valley': ('Mid Valley Megamall', 'Mid Valley, Kuala Lumpur'),
            'quill city mall': ('Quill City Mall', 'Kuala Lumpur'),
            'mytown shopping centre': ('MyTown Shopping Centre', 'Cheras, Kuala Lumpur'),
            'mytown': ('MyTown Shopping Centre', 'Cheras, Kuala Lumpur'),
            'setia city convention centre': ('Setia City Convention Centre', 'Shah Alam, Selangor'),
            'setia city': ('Setia City Convention Centre', 'Shah Alam, Selangor'),
            'sccc': ('Setia City Convention Centre', 'Shah Alam, Selangor'),
            'spice arena': ('Spice Arena', 'Penang'),
            'klpac': ('KLPac', 'Kuala Lumpur'),
            'kuala lumpur performing arts centre': ('KLPac', 'Kuala Lumpur'),
            'tun hussein onn': ('Tun Hussein Onn Theatre', 'Kuala Lumpur'),
            'mpob': ('MPOB Auditorium', 'Kuala Lumpur'),
        }
        
        self.month_map = {
            'JAN': 'January', 'FEB': 'February', 'MAR': 'March', 'APR': 'April',
            'MAY': 'May', 'JUN': 'June', 'JUL': 'July', 'AUG': 'August',
            'SEP': 'September', 'OCT': 'October', 'NOV': 'November', 'DEC': 'December',
            'JANUARY': 'January', 'FEBRUARY': 'February', 'MARCH': 'March', 'APRIL': 'April',
            'JUNE': 'June', 'JULY': 'July', 'AUGUST': 'August', 'SEPTEMBER': 'September',
            'OCTOBER': 'October', 'NOVEMBER': 'November', 'DECEMBER': 'December'
        }
    
    def fetch_with_retry(self, url: str) -> Optional[requests.Response]:
        #"""Fetch URL with retry and caching"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                response = requests.Response()
                response._content = cached_data.encode()
                response.status_code = 200
                response.encoding = 'utf-8'
                return response
        
        # Fetch with retry
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
                if response.status_code == 200:
                    self.cache[cache_key] = (response.text, time.time())
                    return response
                elif response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except:
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
                return None
        return None
    
    def parse_date(self, date_text: str) -> str:
        """Enhanced date parsing"""
        if not date_text or date_text.strip().lower() in ['tba', 'to be announced']:
            return 'TBA'
        
        date_text = date_text.strip()
        
        # Pattern 1: "22 FEB 2026"
        pattern1 = re.search(r'(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|JANUARY|FEBRUARY|MARCH|APRIL|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})', date_text.upper())
        if pattern1:
            day, month_abbr, year = pattern1.groups()
            month = self.month_map[month_abbr.upper()]
            return f"{day} {month} {year}"
        
        # Pattern 2: "February 22, 2026"
        pattern2 = re.search(r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|JANUARY|FEBRUARY|MARCH|APRIL|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{1,2}),?\s+(\d{4})', date_text.upper())
        if pattern2:
            month_abbr, day, year = pattern2.groups()
            month = self.month_map[month_abbr.upper()]
            return f"{day} {month} {year}"
        
        # Pattern 3: "22/02/2026"
        pattern3 = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', date_text)
        if pattern3:
            day, month_num, year = pattern3.groups()
            try:
                month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                month = month_names[int(month_num)]
                return f"{day} {month} {year}"
            except:
                pass
        
        # Pattern 4: "2026-02-22"
        pattern4 = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_text)
        if pattern4:
            year, month_num, day = pattern4.groups()
            try:
                month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                month = month_names[int(month_num)]
                return f"{day} {month} {year}"
            except:
                pass
        
        # Pattern 5: "February 2026"
        pattern5 = re.search(r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|JANUARY|FEBRUARY|MARCH|APRIL|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})', date_text.upper())
        if pattern5:
            month_abbr, year = pattern5.groups()
            month = self.month_map[month_abbr.upper()]
            return f"{month} {year}"
        
        # Try to extract year
        year_match = re.search(r'\b(202[4-9]|203[0-9])\b', date_text)
        if year_match:
            return f"TBA {year_match.group(1)}"
        
        return 'TBA'

    def extract_venue_smart(self, text: str) -> Tuple[str, str]:
        """IMPROVED: Smart venue and city extraction with database matching"""
        text_lower = text.lower()
        
        # IMPROVED: Check venue database first for exact matches
        for venue_key, (venue_name, full_location) in self.venue_database.items():
            if venue_key in text_lower:
                return (venue_name, full_location)
        
        # NEW: Try to find venue names from the text itself
        # Look for venue names in the text (capitalized words followed by venue types)
        venue_patterns = [
            r'([A-Z][a-zA-Z\s\-&\.]+?(?:Arena|Stadium|Hall|Centre|Center|Auditorium|Club|Theatre|Theater|Convention|Lounge|Room|Plaza))',
            r'\b(at|@|venue|location)\s*:?\s*([A-Z][a-zA-Z\s\-&\.]+?(?:Arena|Stadium|Hall|Centre|Center))',
            r'\b([A-Z][a-zA-Z\s\-&\.]{3,30})\s+(?:Concert|Music|Event|Show)\s+(?:Hall|Venue|Center)',
        ]
        
        # Try to extract venue from text patterns
        best_venue = None
        best_city = None
        
        for pattern in venue_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # For patterns with groups
                    venue_candidate = match[-1].strip()
                else:
                    venue_candidate = match.strip()
                
                # Validate venue candidate
                if (10 < len(venue_candidate) < 80 and 
                    not venue_candidate.lower().endswith(('concert', 'event', 'show', 'tour')) and
                    venue_candidate.count(' ') < 8):  # Reasonable word count
                    
                    best_venue = venue_candidate
                    
                    # Try to determine city
                    if 'kuala lumpur' in text_lower or 'kl' in text_lower:
                        best_city = 'Kuala Lumpur'
                    elif 'penang' in text_lower:
                        best_city = 'Penang'
                    elif 'genting' in text_lower or 'highlands' in text_lower:
                        best_city = 'Genting Highlands'
                    elif 'johor' in text_lower or 'bahru' in text_lower:
                        best_city = 'Johor Bahru'
                    elif 'shah alam' in text_lower:
                        best_city = 'Shah Alam, Selangor'
                    elif 'selangor' in text_lower:
                        best_city = 'Selangor'
                    else:
                        best_city = 'Malaysia'
                    
                    break
            
            if best_venue:
                break
        
        # Fallback: Check known venues (old method)
        if not best_venue:
            for venue in self.known_venues:
                if venue in text_lower:
                    best_venue = venue.title()
                    if 'penang' in text_lower:
                        best_city = 'Penang'
                    elif 'johor' in text_lower:
                        best_city = 'Johor Bahru'
                    elif 'genting' in text_lower:
                        best_city = 'Genting Highlands'
                    elif 'shah alam' in text_lower:
                        best_city = 'Shah Alam, Selangor'
                    else:
                        best_city = 'Kuala Lumpur'
                    break
        
        # If still no venue, try to extract from common patterns
        if not best_venue:
            # Look for "Venue:" pattern
            venue_match = re.search(r'venue\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
            if venue_match:
                venue_candidate = venue_match.group(1).strip()
                if 5 < len(venue_candidate) < 100:
                    best_venue = venue_candidate
                    best_city = 'Kuala Lumpur'  # Default
        
        # If still nothing, try to guess city
        if not best_venue:
            city_match = re.search(r'(Kuala Lumpur|KL|Penang|Johor Bahru|Genting Highlands|Selangor|Shah Alam)', text, re.I)
            if city_match:
                city = city_match.group(1)
                if city.lower() == 'kl':
                    city = 'Kuala Lumpur'
                return ('TBD (Check Official Site)', city)
        
        return (best_venue or 'TBD (Check Official Site)', best_city or 'Malaysia')
            
    
    def extract_event_details(self, url: str, source: str) -> Dict[str, str]:
        #"""IMPROVED: Fetch event detail page for more info - ENHANCED for RW Genting"""
        details = {'date': 'TBA', 'venue': 'Malaysia', 'city': 'Malaysia'}
        
        try:
            response = self.fetch_with_retry(url)
            if not response or response.status_code != 200:
                return details
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try inline JS variables
            scripts = soup.find_all('script')
            for script in scripts:
                text = script.get_text()
                match = re.search(r'(20\d{2}-\d{2}-\d{2})', text)
                if match:
                    parsed = self.parse_date(match.group(1))
                    if parsed != 'TBA':
                        details['date'] = parsed
                        break

            # SPECIAL HANDLING for RW Genting
            if source == 'Resorts World Genting' or 'rwgenting.com' in url:
                # Method 1: Look for specific date elements
                date_elements = soup.find_all(['div', 'span', 'p', 'time'], class_=re.compile(r'date|time|when', re.I))
                for elem in date_elements:
                    text = elem.get_text(strip=True)
                    parsed = self.parse_date(text)
                    if parsed != 'TBA':
                        details['date'] = parsed
                        break
                
                # Method 2: Look for datetime attributes
                if details['date'] == 'TBA':
                    time_elem = soup.find('time', datetime=True)
                    if time_elem:
                        datetime_val = time_elem.get('datetime', '')
                        parsed = self.parse_date(datetime_val)
                        if parsed != 'TBA':
                            details['date'] = parsed
                
                # Method 3: Search meta tags
                if details['date'] == 'TBA':
                    meta_date = soup.find('meta', property='event:start_date')
                    if not meta_date:
                        meta_date = soup.find('meta', attrs={'name': 'date'})
                    if meta_date:
                        content = meta_date.get('content', '')
                        parsed = self.parse_date(content)
                        if parsed != 'TBA':
                            details['date'] = parsed
                
                # Method 4: Look in headings and main content
                if details['date'] == 'TBA':
                    headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                    for heading in headings:
                        text = heading.get_text()
                        parsed = self.parse_date(text)
                        if parsed != 'TBA':
                            details['date'] = parsed
                            break
                
                # Method 5: Search entire page more aggressively
                if details['date'] == 'TBA':
                    page_text = soup.get_text()
                    # Look for date patterns with context words
                    date_contexts = re.findall(r'(?:date|when|time|show|event|performance)[\s:]+([^\n]{0,100})', page_text, re.I)
                    for context in date_contexts:
                        parsed = self.parse_date(context)
                        if parsed != 'TBA':
                            details['date'] = parsed
                            break
                
                # Method 6: Extract from inline JS / dataLayer (RW Genting SPECIFIC)
                if details['date'] == 'TBA':
                    scripts = soup.find_all('script')
                    for script in scripts:
                        text = script.string or ''
                        if not text:
                            continue

                        # Look for ISO dates or eventDate
                        match = re.search(r'(202\d[-/]\d{1,2}[-/]\d{1,2})', text)
                        if match:
                            parsed = self.parse_date(match.group(1))
                            if parsed != 'TBA':
                                details['date'] = parsed
                                break


                # RW Genting venues
                page_text_lower = soup.get_text().lower()
                if 'arena of stars' in page_text_lower:
                    details['venue'] = 'Arena of Stars'
                    details['city'] = 'Genting Highlands'
                elif 'genting international showroom' in page_text_lower:
                    details['venue'] = 'Genting International Showroom'
                    details['city'] = 'Genting Highlands'
                elif 'cloud 9' in page_text_lower or 'cloud nine' in page_text_lower:
                    details['venue'] = 'Cloud 9'
                    details['city'] = 'Genting Highlands'
                else:
                    details['venue'] = 'Arena of Stars'
                    details['city'] = 'Genting Highlands'
                
                return details
            
            # STANDARD HANDLING for other sources
            page_text = soup.get_text()
            
            # Try JSON-LD structured data first
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if isinstance(data, dict):
                        if 'startDate' in data:
                            date_str = data['startDate']
                            parsed_date = self.parse_date(date_str)
                            if parsed_date != 'TBA':
                                details['date'] = parsed_date
                        
                        if 'location' in data:
                            location = data['location']
                            if isinstance(location, dict) and 'name' in location:
                                venue, city = self.extract_venue_smart(location['name'])
                                if venue != 'Malaysia':
                                    details['venue'] = venue
                                    details['city'] = city
                except:
                    pass
            
            # Extract date from page text (first 5000 chars for better coverage)
            if details['date'] == 'TBA':
                date_text = self.parse_date(page_text[:5000])
                if date_text != 'TBA':
                    details['date'] = date_text
            
            # Extract venue (first 5000 chars)
            if details['venue'] == 'Malaysia':
                venue, city = self.extract_venue_smart(page_text[:5000])
                if venue != 'Malaysia':
                    details['venue'] = venue
                    details['city'] = city
            
        except Exception as e:
            print(f"Error extracting details from {url}: {e}")
            pass
        
        return details
    
    def scrape_livenation(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape LiveNation Malaysia"""
        events = []
        try:
            url = "https://www.livenation.my/"
            response = self.fetch_with_retry(url)
            if not response:
                return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            event_links = soup.find_all('a', href=re.compile(r'/event/'))
            seen_events = set()
            
            for link in event_links[:15]:
                try:
                    event_url = link.get('href', '')
                    if not event_url or event_url in seen_events:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://www.livenation.my' + event_url
                    seen_events.add(event_url)
                    
                    title_elem = link.find(['h2', 'h3', 'h4']) or link
                    title = re.sub(r'\s+', ' ', title_elem.get_text(strip=True))
                    
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    # Get date
                    parent = link.parent
                    date_text = 'TBA'
                    if parent:
                        parent_text = parent.get_text()
                        date_text = self.parse_date(parent_text)
                    
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    img_elem = link.find('img')
                    image_url = img_elem.get('src', '') if img_elem else ''
                    if image_url and not image_url.startswith('http'):
                        image_url = 'https://www.livenation.my' + image_url
                        
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': 'Kuala Lumpur',
                        'city': 'Kuala Lumpur',
                        'url': event_url,
                        'image': image_url,
                        'source': 'LiveNation Malaysia'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"LiveNation error: {e}")
        
        return events
    
    def scrape_ticket2u(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape Ticket2U"""
        events = []
        try:
            url = "https://www.ticket2u.com.my/event/list/?cc=entertainment&scc=concert"
            response = self.fetch_with_retry(url)
            if not response:
                return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            containers = soup.find_all('div', class_=re.compile(r'event|card|item', re.I))[:20]
            seen_urls = set()
            
            for container in containers:
                try:
                    link = container.find('a', href=True)
                    if not link:
                        continue
                    
                    event_url = link.get('href', '')
                    if not event_url or '/event/' not in event_url or event_url in seen_urls:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://www.ticket2u.com.my' + event_url
                    seen_urls.add(event_url)
                    
                    title = container.get('title', '')
                    if not title:
                        title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                        title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
                    
                    title = re.sub(r'\s+', ' ', title).strip()
                    
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    container_text = container.get_text()
                    date_text = self.parse_date(container_text)
                    
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    img = container.find('img')
                    image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                    if image_url and not image_url.startswith('http'):
                        image_url = 'https://www.ticket2u.com.my' + image_url
                    
                    venue, city = self.extract_venue_smart(container_text)
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': venue,
                        'city': city,
                        'url': event_url,
                        'image': image_url,
                        'source': 'Ticket2U'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"Ticket2U error: {e}")
        
        return events
    
    def scrape_golive(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape GoLive Asia"""
        events = []
        try:
            url = "https://www.golive-asia.com"
            response = self.fetch_with_retry(url)
            if not response:
                return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            event_links = soup.find_all('a', href=re.compile(r'/event|/concert|/show'))[:15]
            seen_urls = set()
            
            for link in event_links:
                try:
                    event_url = link.get('href', '')
                    if not event_url or event_url in seen_urls:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://www.golive-asia.com' + event_url
                    seen_urls.add(event_url)
                    
                    title = re.sub(r'\s+', ' ', link.get_text(strip=True) or link.get('title', 'Event'))
                    
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    parent = link.parent
                    date_text = 'TBA'
                    if parent:
                        date_text = self.parse_date(parent.get_text())
                    
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    img = link.find('img')
                    image_url = img.get('src', '') if img else ''
                    if image_url and not image_url.startswith('http'):
                        image_url = 'https://www.golive-asia.com' + image_url
                        
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': 'Malaysia',
                        'city': 'Malaysia',
                        'url': event_url,
                        'image': image_url,
                        'source': 'GoLive Asia'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"GoLive error: {e}")
        
        return events
    
    def scrape_etix(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape Etix Malaysia"""
        events = []
        try:
            url = "https://www.etix.my"
            response = self.fetch_with_retry(url)
            if not response:
                return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            containers = soup.find_all('div', class_=re.compile(r'event|show', re.I))[:20]
            seen_urls = set()
            
            for container in containers:
                try:
                    link = container.find('a', href=True)
                    if not link:
                        continue
                    
                    event_url = link.get('href', '')
                    if not event_url or event_url in seen_urls:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://www.etix.my' + event_url
                    seen_urls.add(event_url)
                    
                    title = container.get('title', '')
                    if not title:
                        title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                        title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
                    
                    title = re.sub(r'\s+', ' ', title).strip()
                    if len(title) < 3:
                        continue
                    
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    container_text = container.get_text()
                    date_text = self.parse_date(container_text)
                    
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    img = container.find('img')
                    image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                    if image_url and not image_url.startswith('http'):
                        image_url = 'https://www.etix.my' + image_url
                    
                    venue, city = self.extract_venue_smart(container_text)
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': venue,
                        'city': city,
                        'url': event_url,
                        'image': image_url,
                        'source': 'Etix Malaysia'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"Etix error: {e}")
        
        return events
    
    def scrape_starplanet(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape Star Planet"""
        events = []
        try:
            url = "https://starplanet.com.my"
            response = self.fetch_with_retry(url)
            if not response:
                return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            elements = soup.find_all('a', href=re.compile(r'/event|/concert|/show', re.I))[:20]
            seen_urls = set()
            
            for element in elements:
                try:
                    event_url = element.get('href', '')
                    if not event_url or event_url in seen_urls:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://starplanet.com.my' + event_url
                    seen_urls.add(event_url)
                    
                    title = element.get('title', '')
                    if not title:
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                        title = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)
                    
                    title = re.sub(r'\s+', ' ', title).strip()
                    if len(title) < 3:
                        continue
                    
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    search_elem = element.parent if element.parent else element
                    search_text = search_elem.get_text()
                    date_text = self.parse_date(search_text)
                    
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    img = element.find('img')
                    image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                    if image_url and not image_url.startswith('http'):
                        image_url = 'https://starplanet.com.my' + image_url
                    
                    venue, city = self.extract_venue_smart(search_text)
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': venue,
                        'city': city,
                        'url': event_url,
                        'image': image_url,
                        'source': 'Star Planet'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"Star Planet error: {e}")
        
        return events
    
    def scrape_stubhub(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape StubHub Malaysia"""
        events = []
        try:
            url = "https://www.stubhub.com.my/concert-tickets/grouping/189"
            response = self.fetch_with_retry(url)
            if not response:
                url = "https://www.stubhub.com.my"
                response = self.fetch_with_retry(url)
                if not response:
                    return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            elements = soup.find_all('a', href=re.compile(r'/event/|/concert/|tickets', re.I))[:20]
            seen_urls = set()
            
            for element in elements:
                try:
                    event_url = element.get('href', '')
                    if not event_url or event_url in seen_urls:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://www.stubhub.com.my' + event_url
                    seen_urls.add(event_url)
                    
                    title = element.get('title', '') or element.get('aria-label', '')
                    if not title:
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                        title = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)
                    
                    title = re.sub(r'\s+', ' ', title).strip()
                    title = re.sub(r'\s*tickets\s*$', '', title, flags=re.I).strip()
                    
                    if len(title) < 3:
                        continue
                    
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    search_text = element.get_text()
                    date_text = self.parse_date(search_text)
                    
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    img = element.find('img')
                    image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                    if image_url and not image_url.startswith('http') and image_url:
                        image_url = 'https://www.stubhub.com.my' + image_url
                    
                    venue, city = self.extract_venue_smart(search_text)
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': venue,
                        'city': city,
                        'url': event_url,
                        'image': image_url,
                        'source': 'StubHub Malaysia'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"StubHub error: {e}")
        
        return events
    
    def scrape_ticketek(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape Ticketek Malaysia"""
        events = []
        try:
            url = "https://premier.ticketek.com.my"
            response = self.fetch_with_retry(url)
            if not response:
                return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find event containers - Ticketek uses specific structures
            elements = (
                soup.find_all('a', href=re.compile(r'/event|/show|/concert', re.I)) or
                soup.find_all('div', class_=re.compile(r'event|show|card', re.I))
            )
            
            seen_urls = set()
            
            for element in elements[:20]:
                try:
                    # Get link
                    link = element if element.name == 'a' else element.find('a', href=True)
                    if not link:
                        continue
                    
                    event_url = link.get('href', '')
                    if not event_url or event_url in seen_urls:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://premier.ticketek.com.my' + event_url
                    seen_urls.add(event_url)
                    
                    # Get title
                    title = element.get('title', '') or element.get('alt', '')
                    if not title:
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                        title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
                    
                    title = re.sub(r'\s+', ' ', title).strip()
                    
                    if len(title) < 3:
                        continue
                    
                    # Filter by keywords
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    # Get date
                    search_text = element.get_text()
                    date_text = self.parse_date(search_text)
                    
                    # Filter by date
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    # Get image
                    img = element.find('img')
                    image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                    if image_url and not image_url.startswith('http') and image_url:
                        image_url = 'https://premier.ticketek.com.my' + image_url
                    
                    # Get venue
                    venue, city = self.extract_venue_smart(search_text)
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': venue,
                        'city': city,
                        'url': event_url,
                        'image': image_url,
                        'source': 'Ticketek Malaysia'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"Ticketek error: {e}")
        
        return events
    
    def scrape_rwgenting(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape Resorts World Genting - ENHANCED"""
        events = []
        try:
            url = "https://www.rwgenting.com/en/entertainment/shows-and-events.html"
            response = self.fetch_with_retry(url)
            if not response:
                return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            elements = (
                soup.find_all('div', class_=re.compile(r'event|show|card|item|promo', re.I)) +
                soup.find_all('a', href=re.compile(r'/event|/show|/entertainment', re.I))
            )
            
            seen_urls = set()
            
            for element in elements[:25]:
                try:
                    link = element if element.name == 'a' else element.find('a', href=True)
                    if not link:
                        continue
                    
                    event_url = link.get('href', '')
                    if not event_url or event_url in seen_urls:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://www.rwgenting.com' + event_url
                    seen_urls.add(event_url)
                    
                    title = element.get('title', '') or element.get('alt', '')
                    if not title:
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                        title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
                    
                    title = re.sub(r'\s+', ' ', title).strip()
                    
                    if len(title) < 3:
                        continue
                    
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    # Try to extract date from container first
                    search_text = element.get_text()
                    date_text = self.parse_date(search_text)
                    
                    # Also check for data attributes
                    if date_text == 'TBA':
                        date_attr = element.get('data-date') or element.get('data-start-date')
                        if date_attr:
                            date_text = self.parse_date(date_attr)
                    
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    img = element.find('img')
                    image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                    if image_url and not image_url.startswith('http') and image_url and not image_url.startswith('//'):
                        image_url = 'https://www.rwgenting.com' + image_url
                    elif image_url and image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    
                    venue = 'Arena of Stars'
                    city = 'Genting Highlands'
                    
                    search_text_lower = search_text.lower()
                    if 'genting international showroom' in search_text_lower:
                        venue = 'Genting International Showroom'
                    elif 'cloud 9' in search_text_lower or 'cloud nine' in search_text_lower:
                        venue = 'Cloud 9'
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': venue,
                        'city': city,
                        'url': event_url,
                        'image': image_url,
                        'source': 'Resorts World Genting'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"RW Genting error: {e}")
        
        return events
    
    def scrape_bookmyshow(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Scrape BookMyShow Malaysia"""
        events = []
        try:
            url = "https://my.bookmyshow.com/explore/events-kuala-lumpur"
            response = self.fetch_with_retry(url)
            if not response:
                url = "https://my.bookmyshow.com/explore/concerts-kuala-lumpur"
                response = self.fetch_with_retry(url)
                if not response:
                    return events
            
            soup = BeautifulSoup(response.content, 'html.parser')
            elements = soup.find_all('a', href=re.compile(r'/events/|/concerts/', re.I))[:20]
            seen_urls = set()
            
            for element in elements:
                try:
                    event_url = element.get('href', '')
                    if not event_url or event_url in seen_urls:
                        continue
                    
                    if not event_url.startswith('http'):
                        event_url = 'https://my.bookmyshow.com' + event_url
                    seen_urls.add(event_url)
                    
                    title = element.get('title', '') or element.get('alt', '')
                    if not title:
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                        title = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)
                    
                    title = re.sub(r'\s+', ' ', title).strip()
                    
                    if len(title) < 3:
                        continue
                    
                    if keywords and keywords.lower() not in title.lower():
                        continue
                    
                    search_text = element.get_text()
                    date_text = self.parse_date(search_text)
                    
                    if date and date.lower() not in date_text.lower():
                        continue
                    
                    img = element.find('img')
                    image_url = img.get('src', '') or img.get('data-src', '') if img else ''
                    if image_url and not image_url.startswith('http') and image_url and not image_url.startswith('//'):
                        image_url = 'https://my.bookmyshow.com' + image_url
                    elif image_url and image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    
                    venue, city = self.extract_venue_smart(search_text)
                    artist = self.artist_recognizer.extract_artist_from_title(title)

                    events.append({
                        'name': title,
                        'artist': artist,
                        'date': date_text,
                        'venue': venue,
                        'city': city,
                        'url': event_url,
                        'image': image_url,
                        'source': 'BookMyShow Malaysia'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"BookMyShow error: {e}")
        
        return events
    
    def venue_confidence(self, venue: str) -> int:
        if venue in ['Malaysia']:
            return 0
        if venue in ['Kuala Lumpur']:
            return 1
        if 'Arena' in venue or 'Stadium' in venue or 'Hall' in venue:
            return 3
        return 2

    def is_duplicate_event(self, event1: Dict, event2: Dict) -> bool:
        # Artist match = STRONG signal
        if event1.get('artist') and event2.get('artist'):
            if event1['artist'].lower() == event2['artist'].lower():
                # Same artist + same date OR both TBA
                if event1['date'] == event2['date'] or 'TBA' in event1['date']:
                    return True

        #"""Check if two events are duplicates with strict matching"""
        name1 = event1.get('name', '').lower().strip()
        name2 = event2.get('name', '').lower().strip()
        
        # Remove common noise words and normalize
        noise_words = {'concert', 'live', 'tour', 'show', 'event', 'the', 'in', 'at', '&', 'and', 
                      'presents', 'featuring', 'with', 'special', 'guest', '2025', '2026', '2027',
                      'malaysia', 'kuala', 'lumpur', 'kl', 'more', 'info', 'pulse', 'on'}
        
        # Clean and normalize names
        def clean_name(name):
            # Remove special characters and extra spaces
            name = re.sub(r'[^\w\s]', ' ', name)
            name = re.sub(r'\s+', ' ', name).strip()
            # Remove noise words
            words = [w for w in name.split() if w not in noise_words]
            return ' '.join(words)
        
        clean1 = clean_name(name1)
        clean2 = clean_name(name2)
        
        # Exact match after cleaning
        if clean1 == clean2:
            return True
        
        # Check if one name contains the other (for variations)
        if clean1 in clean2 or clean2 in clean1:
            if len(clean1) > 10 or len(clean2) > 10:  # Avoid matching too short names
                return True
        
        # Word-based similarity
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        similarity = intersection / union if union > 0 else 0
        
        # More strict similarity threshold
        if similarity > 0.8:
            return True
        
        # If very similar (>60%) and same date, it's duplicate
        if similarity > 0.6:
            date1 = event1.get('date', '')
            date2 = event2.get('date', '')
            # Only match if both have actual dates (not TBA)
            if date1 == date2 and 'TBA' not in date1:
                return True
        
        return False
    
    def is_valid_event(self, event: Dict) -> bool:
        """Validate event quality"""
        name = event.get('name', '').lower().strip()
        
        generic_terms = ['event', 'concert', 'show', 'events', 'concerts', 'shows', 'buy tickets', 'get tickets', 'view all', 'see all', 'more events']
        
        if name in generic_terms or len(name) < 5:
            return False
        
        if all(word in ['concert', 'event', 'show', 'ticket', 'and', '&', 'the'] for word in name.split()):
            return False
        
        return True

    def search_concerts(self, keywords: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        all_events = []
        
        print("Scraping sources in parallel...")
        
        # Parallel scraping
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(self.scrape_livenation, keywords, date): 'LiveNation',
                executor.submit(self.scrape_ticket2u, keywords, date): 'Ticket2U',
                executor.submit(self.scrape_golive, keywords, date): 'GoLive',
                executor.submit(self.scrape_etix, keywords, date): 'Etix',
                executor.submit(self.scrape_starplanet, keywords, date): 'StarPlanet',
                executor.submit(self.scrape_stubhub, keywords, date): 'StubHub',
                executor.submit(self.scrape_bookmyshow, keywords, date): 'BookMyShow',
                executor.submit(self.scrape_ticketek, keywords, date): 'Ticketek',
                executor.submit(self.scrape_rwgenting, keywords, date): 'RW Genting',
            }
            
            for future in as_completed(futures):
                source = futures[future]
                try:
                    events = future.result()
                    print(f"✓ {source}: {len(events)} events")
                    all_events.extend(events)
                except Exception as e:
                    print(f"✗ {source}: Error")
        
        # Remove invalid events
        all_events = [e for e in all_events if self.is_valid_event(e)]
        
        # Remove duplicates with improved algorithm
        unique_events = []
        for event in all_events:
            is_dup = False
            for unique_event in unique_events:
                if self.is_duplicate_event(event, unique_event):
                    # Keep the one with better data (more specific date, better venue)
                    event_score = self.calculate_event_score(event)
                    unique_score = self.calculate_event_score(unique_event)
                    
                    if event_score > unique_score:
                        unique_events.remove(unique_event)
                        unique_events.append(event)
                    
                    is_dup = True
                    break
            
            if not is_dup:
                unique_events.append(event)
        
        print(f"\nFound {len(unique_events)} unique events")
        
        # IMPROVED: DEEP DETAIL FETCHING for ALL events
        print(f"Fetching detailed info for ALL {len(unique_events)} events...")
        
        # Use parallel fetching for speed
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(self.extract_event_details, event['url'], event['source']): event
                for event in unique_events
            }
            
            for future in as_completed(futures):
                event = futures[future]
                try:
                    details = future.result()
                    
                    # Update with better details if found
                    if details['date'] != 'TBA' and (event['date'] == 'TBA' or event['date'].startswith('TBA')):
                        event['date'] = details['date']
                        print(f"  ✓ Got date for {event['name'][:40]}: {details['date']}")
                    
                    if self.venue_confidence(details['venue']) > self.venue_confidence(event['venue']):
                        event['venue'] = details['venue']
                        event['city'] = details['city']

                        print(f"  ✓ Got venue for {event['name'][:40]}: {details['venue']}")
                except:
                    pass
        
        # IMPROVED: Sort but KEEP TBA events (don't filter them out!)
        print(f"\nSorting events (TBA events will appear at the end)...")
        
        def sort_key(e):
            date_str = e['date']
            
            # TBA events go to the end (but are still included!)
            if date_str.startswith('TBA'):
                return (1, 999999, date_str)  # Sort TBA events by their string
            
            # Parse date for sorting
            try:
                date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_str)
                if date_match:
                    day, month, year = date_match.groups()
                    month_num = list(self.month_map.values()).index(month) + 1
                    date_obj = datetime(int(year), month_num, int(day))
                    days_from_now = (date_obj - datetime.now()).days
                    return (0, days_from_now, date_str)
            except:
                pass
            
            return (1, 999999, date_str)
        
        unique_events.sort(key=sort_key)
        artist_query = ''
        
        # Prioritize keyword matches
        if keywords:
            artist_query = self.artist_recognizer.extract_artist_from_query(keywords)

        unique_events.sort(
            key=lambda e: (
                0 if artist_query and artist_query.lower() == e.get('artist', '').lower() else 1,
                0 if keywords and keywords.lower() in e['name'].lower() else 1,
                sort_key(e)
            )
        )

        
        print(f"✅ Returning {len(unique_events[:20])} results (INCLUDING TBA events)\n")
        return unique_events[:20]
    
    def calculate_event_score(self, event: Dict) -> int:
        """Calculate score for event quality (higher = better)"""
        score = 0
        
        # Has specific date (not TBA)
        if not event['date'].startswith('TBA'):
            score += 50
            # Has full date (day + month + year)
            if re.search(r'\d{1,2}\s+\w+\s+\d{4}', event['date']):
                score += 25
        
        # Has specific venue (not generic)
        if event['venue'] not in ['Malaysia', 'Kuala Lumpur']:
            score += 25
        
        return score