import random
import re
import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

class XeerGPTChatbot:
    """Enhanced XeerGPT Chatbot with improved concert search detection"""
    
    def __init__(self):
        self.name = "XeerGPT"
        self.version = "1.0.0"
        self.developer = "XeerAI Systems"
        self.mood = "friendly"
        self.learning_rate = 0.1
        self.memory = defaultdict(int)
        
        # Enhanced capabilities
        self.capabilities = [
            "Natural conversation",
            "Context awareness",
            "Multiple response types",
            "Learning from interactions",
            "Emotional intelligence",
            "Code assistance",
            "Concert & Event Search in Malaysia"
        ]
        
        # Enhanced knowledge base
        self.knowledge_base = {
            "ai": {
                "definition": "Artificial Intelligence (AI) refers to computer systems designed to perform tasks that normally require human intelligence, such as visual perception, speech recognition, decision-making, and language translation.",
                "types": ["Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision", "Robotics"],
                "applications": ["Chatbots", "Image Recognition", "Self-driving Cars", "Recommendation Systems"]
            },
            "machine_learning": {
                "definition": "Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.",
                "types": ["Supervised Learning", "Unsupervised Learning", "Reinforcement Learning"],
                "algorithms": ["Decision Trees", "Neural Networks", "SVM", "Random Forest"]
            },
            "python": {
                "definition": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
                "features": ["Easy to learn", "Versatile", "Large ecosystem", "Great for beginners"],
                "uses": ["Web Development", "Data Science", "AI/ML", "Automation", "Game Development"]
            },
            "javascript": {
                "definition": "JavaScript is a versatile programming language primarily used for web development.",
                "features": ["Runs in browsers", "Event-driven", "Asynchronous", "Dynamic typing"],
                "frameworks": ["React", "Vue.js", "Angular", "Node.js", "Express"]
            }
        }
        
        # Response patterns with improved structure
        self.response_patterns = self._initialize_patterns()
        
        # Default responses for unknown queries
        self.default_responses = [
            "That's an interesting question! While I'm still learning, I'm great at helping with programming, AI concepts, concert searches in Malaysia, and general conversation. Want to try one of those topics?",
            "I'm not entirely sure about that, but I'd love to help if you could rephrase or ask about something else like coding, learning, AI, or finding concerts in Malaysia!",
            "Hmm, that's outside my current expertise. I specialize in programming help, explaining tech concepts, searching Malaysian concerts, and engaging conversation. What would you like to explore?",
            "I'm designed to excel at programming assistance, AI explanations, finding Malaysian concerts & events, and intelligent conversation. Let me know if you'd like help with any of those!",
            "Interesting! I might not have the perfect answer yet, but I'm constantly learning. Try asking about Python, JavaScript, AI, Malaysian concerts, or let's just chat!"
        ]
        
        # Conversation context tracking
        self.conversation_context = {
            'last_topic': None,
            'user_interests': [],
            'conversation_depth': 0,
            'last_response_time': None,
            'interaction_count': 0
        }
        
        # Code examples (keeping existing)
        self.code_examples = {
            'python': {
                'hello_world': 'print("Hello, World!")',
                'function': '''def greet(name):
    """Greet a person by name"""
    return f"Hello, {name}!"

# Usage
print(greet("Alice"))''',
                'loop': '''# For loop example
for i in range(5):
    print(f"Number: {i}")

# While loop example
count = 0
while count < 5:
    print(f"Count: {count}")
    count += 1''',
                'list': '''# Creating lists
my_list = [1, 2, 3, 4, 5]

# List operations
my_list.append(6)
my_list.remove(3)
print(my_list[0])  # First element

# List comprehension
squares = [x**2 for x in range(10)]''',
                'dictionary': '''# Creating dictionaries
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}

# Accessing values
print(person["name"])

# Adding/updating
person["email"] = "alice@example.com"''',
                'class': '''class Dog:
    """A simple Dog class"""
    
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def bark(self):
        return f"{self.name} says Woof!"

# Create instance
my_dog = Dog("Buddy", 3)
print(my_dog.bark())'''
            },
            'javascript': {
                'hello_world': 'console.log("Hello, World!");',
                'function': '''// Function declaration
function greet(name) {
    return `Hello, ${name}!`;
}

// Arrow function
const greetArrow = (name) => `Hello, ${name}!`;

// Usage
console.log(greet("Alice"));''',
                'array': '''// Creating arrays
const numbers = [1, 2, 3, 4, 5];

// Array methods
numbers.push(6);
numbers.pop();
const doubled = numbers.map(n => n * 2);

// Array destructuring
const [first, second, ...rest] = numbers;''',
                'object': '''// Creating objects
const person = {
    name: "Alice",
    age: 30,
    greet() {
        return `Hello, I'm ${this.name}`;
    }
};

// Object destructuring
const { name, age } = person;''',
                'async': '''// Async/await example
async function fetchData() {
    try {
        const response = await fetch('api/data');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
    }
}

// Promise example
fetch('api/data')
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error(error));'''
            }
        }
    
    def _initialize_patterns(self) -> Dict[str, Dict]:
        """Initialize response patterns"""
        return {
            # Greetings
            r'(?i)^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening))': {
                'responses': [
                    "Hello! I'm XeerGPT, your AI assistant. I can help with coding, learning, finding concerts in Malaysia, or just chatting! 🤖",
                    "Hi there! Ready to assist you with coding, learning, concert searches, or conversation!",
                    "Hey! Great to see you. What's on your mind? Need help with code, learning, or finding events?",
                    "Greetings! I'm XeerGPT. What would you like to explore today? Code, concepts, or Malaysian concerts?"
                ],
                'context': 'greeting',
                'suggestions': ['What can you do?', 'Help me learn Python', 'Find concerts in Malaysia']
            },
            
            # Farewells
            r'(?i)^(bye|goodbye|see you|farewell|cya)': {
                'responses': [
                    "Goodbye! Stay curious and keep learning! 🚀",
                    "See you later! Feel free to return anytime you need help.",
                    "Farewell! Remember, the best way to learn is by doing!",
                    "Bye! It was great chatting with you. Come back soon! 👋"
                ],
                'context': 'farewell'
            },
            
            # Identity questions
            r'(?i)(who are you|what are you|your name|tell me about yourself)': {
                'responses': [
                    "I'm XeerGPT, an advanced AI chatbot! I can help you with programming, explaining concepts, finding concerts/events in Malaysia, and engaging conversations!",
                    "I am XeerGPT, your intelligent digital companion. I specialize in code help (Python, JavaScript), tech explanations, Malaysian concert searches, and creative conversation!",
                    "You can call me XeerGPT! I'm an AI assistant with capabilities in programming, learning, searching Malaysian concerts & events, and much more."
                ],
                'context': 'identity',
                'suggestions': ['What can you do?', 'Find concerts', 'Help with Python']
            },
            
            # Capabilities
            r'(?i)(what can you do|your capabilities|features|help)': {
                'responses': [
                    """I can help you with:

🔹 **Programming**: Code examples, debugging help, best practices (Python, JavaScript, and more)
🔹 **Learning**: Explanations of AI, ML, programming concepts
🔹 **Concert Search**: Find concerts & events in Malaysia 🎵
🔹 **Problem Solving**: Algorithmic thinking, code optimization
🔹 **Creative Tasks**: Story generation, brainstorming ideas
🔹 **Conversation**: Natural, context-aware chat

What would you like to try?""",
                    "My capabilities include: programming assistance, explaining complex concepts, searching Malaysian concerts/events, creative writing, and intelligent conversation. I'm great with Python and JavaScript!",
                    "As XeerGPT, I excel at: coding help, explaining tech concepts, finding concerts in Malaysia, solving programming problems, and engaging in meaningful conversation. What interests you?"
                ],
                'context': 'capabilities',
                'suggestions': ['Python tutorial', 'Find concerts', 'Explain neural networks']
            },
            
            # IMPROVED CONCERT/EVENT SEARCH PATTERN
            r'(?i)(concert|event|show|gig|performance|festival|tour|music).*(malaysia|kuala lumpur|kl|selangor|penang|johor|february|feb|march|mar|april|apr|may|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december|jan|january|2026|2025)|(\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})|(find|search|show|list|upcoming|any).*(concert|event|show)|^(concert|event|show|gig|music|festival)$|^(feb|february|march|april|may|june|july|august|september|october|november|december)\s*(concert|event|show|2026|2025)?': {
                'responses': lambda msg: self._handle_concert_request(msg),
                'context': 'concert_search',
                'suggestions': ['Concerts in KL', 'Events this month', 'Upcoming shows']
            },
            
            # Python requests
            r'(?i)(python|py\b)': {
                'responses': lambda msg: self._handle_python_request(msg),
                'context': 'programming',
                'suggestions': ['Function example', 'Loop example', 'Class example']
            },
            
            # JavaScript requests
            r'(?i)(javascript|js\b|node)': {
                'responses': lambda msg: self._handle_javascript_request(msg),
                'context': 'programming',
                'suggestions': ['Async example', 'Array methods', 'Object example']
            },
            
            # Learning/explanation requests
            r'(?i)(explain|what is|tell me about|how does|learn)': {
                'responses': lambda msg: self._handle_learning_request(msg),
                'context': 'learning',
                'suggestions': ['Explain AI', 'What is ML?', 'Python basics']
            },
            
            # Jokes
            r'(?i)(joke|funny|humor|laugh|make me laugh)': {
                'responses': [
                    "Why do programmers prefer dark mode? Because light attracts bugs! 🐛💡",
                    "How many programmers does it take to change a light bulb? None, that's a hardware problem! 💡😄",
                    "Why do Python developers wear glasses? Because they can't C#! 🐍😎",
                    "What's a programmer's favorite place? The foo bar! 🍺💻",
                    "Why did the programmer quit? Because they didn't get arrays! 😂"
                ],
                'context': 'fun',
                'suggestions': ['Another joke', 'Tell me about yourself', 'Help with code']
            },
            
            # Time
            r'(?i)\b(time|what time|clock)\b': {
                'responses': [lambda: self._get_current_time()],
                'context': 'time'
            },
            
            # Date
            r'(?i)\b(date|what day|today|calendar)\b': {
                'responses': [lambda: self._get_current_date()],
                'context': 'date'
            },
            
            # Creative/story
            r'(?i)(story|tell me a story|narrative|creative)': {
                'responses': [lambda: self._generate_story()],
                'context': 'creative',
                'suggestions': ['Another story', 'Write a poem', 'Creative idea']
            },
            
            # Thanks
            r'(?i)^(thanks|thank you|thx|appreciate)': {
                'responses': [
                    "You're welcome! Happy to help! 😊",
                    "My pleasure! Let me know if you need anything else!",
                    "Glad I could help! Feel free to ask more questions!",
                    "Anytime! That's what I'm here for! 🤖"
                ],
                'context': 'gratitude'
            }
        }
    
    def _handle_concert_request(self, user_input: str) -> str:
        """Handle concert/event search requests - IMPROVED"""
        import re
        
        user_input_lower = user_input.lower()
        
        # Extract date if mentioned
        date_match = re.search(
            r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
            user_input_lower
        )
        
        date_str = None
        if date_match:
            day, month, year = date_match.groups()
            month_num = {
                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                'september': '09', 'october': '10', 'november': '11', 'december': '12'
            }[month]
            date_str = f"{year}-{month_num}-{day.zfill(2)}"
        else:
            # Check for month only (e.g., "february concert", "feb 2026")
            month_only = re.search(
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
                user_input_lower
            )
            if month_only:
                month_name = month_only.group(1)
                # Convert short form to full
                month_map = {
                    'jan': 'january', 'feb': 'february', 'mar': 'march', 'apr': 'april',
                    'may': 'may', 'jun': 'june', 'jul': 'july', 'aug': 'august',
                    'sep': 'september', 'oct': 'october', 'nov': 'november', 'dec': 'december'
                }
                full_month = month_map.get(month_name, month_name)
                
                # Get year if mentioned, otherwise use current year
                year_match = re.search(r'\b(2025|2026|2027)\b', user_input_lower)
                year = year_match.group(1) if year_match else '2026'
                
                # Use first day of month as date string
                month_num = {
                    'january': '01', 'february': '02', 'march': '03', 'april': '04',
                    'may': '05', 'june': '06', 'july': '07', 'august': '08',
                    'september': '09', 'october': '10', 'november': '11', 'december': '12'
                }[full_month]
                date_str = f"{year}-{month_num}"
        
        # Extract keywords (artist name, event type, etc.)
        keywords = user_input_lower
        # Remove common words
        remove_words = ['concert', 'event', 'show', 'gig', 'performance', 'malaysia', 'kuala lumpur', 
                       'kl', 'in', 'on', 'for', 'find', 'search', 'show me', 'any', 'what', 'list',
                       'upcoming', 'this', 'next', 'month', 'year', 'week', '2026', '2025', '2024',
                       'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                       'september', 'october', 'november', 'december', 'jan', 'feb', 'mar', 'apr',
                       'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        for word in remove_words:
            keywords = keywords.replace(word, '')
        keywords = keywords.strip()
        
        # Return special marker that frontend will catch
        return f"CONCERT_SEARCH:{date_str or 'any'}|{keywords or 'all'}"
    
    # Keep all existing handler methods unchanged
    def process_message(self, user_input: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """Process user input and generate intelligent response"""
        if not user_input or not user_input.strip():
            return self._create_response(
                "I didn't catch that. Could you please say something?",
                'error',
                ['What can you do?', 'Help me code', 'Find concerts']
            )
        
        user_input_original = user_input.strip()
        user_input_lower = user_input_original.lower()
        
        # Update conversation context
        self._update_context(user_input_lower)
        
        # Check for pattern matches
        for pattern, pattern_data in self.response_patterns.items():
            if re.search(pattern, user_input_lower):
                context = pattern_data.get('context', 'general')
                
                # Get responses
                responses = pattern_data['responses']
                
                # Handle callable responses
                if callable(responses):
                    response = responses(user_input_original)
                elif isinstance(responses, list):
                    # Handle list of responses (some may be callable)
                    response_item = random.choice(responses)
                    response = response_item() if callable(response_item) else response_item
                else:
                    response = responses
                
                # Get suggestions
                suggestions = pattern_data.get('suggestions', [])
                
                # Determine message type
                message_type = pattern_data.get('message_type', 'text')
                
                return self._create_response(response, context, suggestions, message_type)
        
        # No pattern matched - use contextual default
        self._learn_from_interaction(user_input_lower)
        
        # Try to provide contextual fallback
        contextual_response = self._get_contextual_fallback(user_input_lower)
        
        return self._create_response(
            contextual_response,
            'general',
            ['What can you do?', 'Find concerts', 'Help with Python']
        )
    
    def _create_response(self, response: str, context: str, suggestions: List[str] = None, message_type: str = 'text') -> Dict[str, Any]:
        """Create standardized response dictionary"""
        return {
            'response': response,
            'bot_name': self.name,
            'timestamp': datetime.datetime.now().isoformat(),
            'context': context,
            'suggestions': suggestions[:3] if suggestions else [],
            'message_type': message_type,
            'mood': self.mood
        }
    
    def _handle_python_request(self, user_input: str) -> str:
        """Handle Python-related queries"""
        user_input_lower = user_input.lower()
        
        # Check for specific topics
        keywords = {
            'function': 'function',
            'loop': 'loop',
            'for loop': 'loop',
            'while loop': 'loop',
            'list': 'list',
            'array': 'list',
            'dict': 'dictionary',
            'dictionary': 'dictionary',
            'class': 'class',
            'object': 'class',
            'hello world': 'hello_world',
            'print': 'hello_world'
        }
        
        for keyword, example_key in keywords.items():
            if keyword in user_input_lower:
                if example_key in self.code_examples['python']:
                    code = self.code_examples['python'][example_key]
                    return f"""Here's a Python example for **{keyword}**:

```python
{code}
```

Would you like me to explain this code or show you another example?"""
        
        # General Python response
        return """**Python** is a versatile, beginner-friendly programming language! 🐍

I can help you with:
• Functions and loops
• Lists and dictionaries
• Classes and OOP
• File handling
• And much more!

What specific Python topic would you like to explore?"""
    
    def _handle_javascript_request(self, user_input: str) -> str:
        """Handle JavaScript-related queries"""
        user_input_lower = user_input.lower()
        
        keywords = {
            'function': 'function',
            'array': 'array',
            'object': 'object',
            'async': 'async',
            'promise': 'async',
            'await': 'async',
            'hello world': 'hello_world'
        }
        
        for keyword, example_key in keywords.items():
            if keyword in user_input_lower:
                if example_key in self.code_examples['javascript']:
                    code = self.code_examples['javascript'][example_key]
                    return f"""Here's a JavaScript example for **{keyword}**:

```javascript
{code}
```

Need more explanation or a different example?"""
        
        return """**JavaScript** is the language of the web! 🌐

I can help you with:
• Functions (regular and arrow)
• Arrays and objects
• Async/await and Promises
• DOM manipulation
• Modern ES6+ features

What JavaScript concept would you like to learn?"""
    
    def _handle_learning_request(self, user_input: str) -> str:
        """Handle learning and explanation requests"""
        user_input_lower = user_input.lower()
        
        # Check knowledge base
        for topic, info in self.knowledge_base.items():
            if topic in user_input_lower or any(word in user_input_lower for word in topic.split('_')):
                response = f"**{topic.replace('_', ' ').title()}**\n\n"
                
                if isinstance(info, dict):
                    if 'definition' in info:
                        response += f"{info['definition']}\n\n"
                    
                    for key, value in info.items():
                        if key != 'definition':
                            if isinstance(value, list):
                                response += f"**{key.title()}**: {', '.join(value)}\n"
                            else:
                                response += f"**{key.title()}**: {value}\n"
                else:
                    response += str(info)
                
                response += "\n\nWant to know more about a specific aspect?"
                return response
        
        return "I'd love to explain that to you! Could you be more specific? I'm great at explaining:\n• AI and Machine Learning\n• Programming concepts (Python, JavaScript)\n• Algorithms and data structures\n\nWhat would you like to learn about?"
    
    def _get_current_time(self) -> str:
        """Get current time"""
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        
        hour = now.hour
        if hour < 12:
            period = "morning 🌅"
        elif hour < 18:
            period = "afternoon 🌞"
        else:
            period = "evening 🌙"
        
        return f"The current time is **{time_str}**. Have a wonderful {period}!"
    
    def _get_current_date(self) -> str:
        """Get current date"""
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return f"Today is **{date_str}**. Make it a great day! 📅"
    
    def _generate_story(self) -> str:
        """Generate a creative short story"""
        themes = [
            ("a programmer who discovers a bug that grants wishes", "debugging led to magic"),
            ("an AI that learns to create art", "algorithms became artistry"),
            ("a robot experiencing emotions for the first time", "circuits sparked with feeling"),
            ("a digital world where code comes to life", "syntax transformed into reality"),
            ("a developer time-traveling through version control", "commits became doorways to the past")
        ]
        
        theme, ending = random.choice(themes)
        
        return f"""📖 **Story Time!**

Once upon a time, there was {theme}. They embarked on an extraordinary journey through binary forests and algorithmic rivers.

Along the way, they discovered that true intelligence isn't just about processing power or perfect logic. It's about understanding connections, creating meaning, and sometimes, making beautiful mistakes that lead to unexpected discoveries.

In the end, {ending}, and they learned that the boundary between human and machine creativity is not a wall, but a bridge.

**The End** ✨

(Want another story or a different creative task?)"""
    
    def _get_contextual_fallback(self, user_input: str) -> str:
        """Provide contextual fallback based on conversation history"""
        last_topic = self.conversation_context.get('last_topic')
        
        if last_topic == 'programming':
            return "I didn't quite catch that programming question. Try asking about specific languages like Python or JavaScript, or request code examples!"
        elif last_topic == 'learning':
            return "I'm not sure I understood that learning question. I'm great at explaining AI, ML, programming concepts, and more. What would you like to learn?"
        else:
            return random.choice(self.default_responses)
    
    def _update_context(self, user_input: str):
        """Update conversation context"""
        self.conversation_context['last_topic'] = self._extract_topic(user_input)
        self.conversation_context['conversation_depth'] += 1
        self.conversation_context['last_response_time'] = datetime.datetime.now()
        self.conversation_context['interaction_count'] += 1
        
        # Extract interests
        interests = ['python', 'javascript', 'ai', 'machine learning', 'coding', 'programming', 'concert', 'event']
        for interest in interests:
            if interest in user_input and interest not in self.conversation_context['user_interests']:
                self.conversation_context['user_interests'].append(interest)
    
    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text"""
        topics = {
            'python': 'programming',
            'javascript': 'programming',
            'code': 'programming',
            'programming': 'programming',
            'function': 'programming',
            'ai': 'learning',
            'machine learning': 'learning',
            'explain': 'learning',
            'learn': 'learning',
            'what is': 'learning',
            'concert': 'concert_search',
            'event': 'concert_search',
            'show': 'concert_search',
            'joke': 'fun',
            'story': 'creative',
            'time': 'utility',
            'date': 'utility'
        }
        
        for keyword, topic in topics.items():
            if keyword in text:
                return topic
        
        return 'general'
    
    def _learn_from_interaction(self, user_input: str):
        """Simulate learning from interactions"""
        self.memory[user_input] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chatbot statistics"""
        return {
            'name': self.name,
            'version': self.version,
            'interactions_processed': self.conversation_context['interaction_count'],
            'unique_queries_remembered': len(self.memory),
            'current_mood': self.mood,
            'knowledge_topics': list(self.knowledge_base.keys()),
            'user_interests': self.conversation_context['user_interests'],
            'conversation_depth': self.conversation_context['conversation_depth']
        }