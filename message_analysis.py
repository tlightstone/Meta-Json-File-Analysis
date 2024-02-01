import json
import glob
from datetime import datetime
import calendar
import emoji
from collections import Counter
import re  # For regular expressions
from textblob import TextBlob
from collections import defaultdict
from datetime import datetime, timezone

# Name: count_phrase_frequency 
# Purpose: To count the frequency of a specific phrase in the message. 
def count_phrase_frequency(messages, phrase):
    phrase = phrase.lower()
    phrase_count = 0
    for message in messages:
        content = message.get('content', '').lower()
        phrase_count += content.count(phrase)
    return phrase_count

# Name: decode_utf8_escapes 
# Purpose: The JSON file that meta uses encodes their emojis using utf8 encoding. 
#          This helper function converts the unicode to be usable. 
def decode_utf8_escapes(text):
    try:
        # Convert Unicode escape sequences to a byte-like object
        byte_sequence = text.encode('latin-1', 'backslashreplace').decode('unicode-escape').encode('latin-1')
        # Decode from UTF-8
        decoded_text = byte_sequence.decode('utf-8', 'ignore')
        return decoded_text
    except Exception as e:
        print(f"Error decoding text: {e}")
        return text

# Name: filter_messages_by_date
# Purpose: Helper function to filter messages by a chosen start date. 
def filter_messages_by_date(file_data, start_date):
    start_timestamp = start_date.timestamp() * 1000  # Convert to milliseconds
    filtered_messages = [message for message in file_data['messages'] if message.get('timestamp_ms', 0) >= start_timestamp]
    file_data['messages'] = filtered_messages
    return file_data

# Name: count_emojis
# Purpose: helper function counts the number of emojis used in the file
def count_emojis(text):
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
    return Counter(emoji_pattern.findall(text))

# Name: parse_json_chat
# Purpose: This is the main parsing function that contains many uses inside it. 
def parse_json_chat(file_data,target_word):

    # Helper function to convert timestamp to readable format
    def convert_timestamp(timestamp_ms):
        # Convert milliseconds to seconds
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)
        day_of_year = timestamp.timetuple().tm_yday
        time_of_day = timestamp.strftime("%H:%M:%S")
        day_of_week = calendar.day_name[timestamp.weekday()]
        return day_of_year, time_of_day, day_of_week
    
    # Function to list all participants of the chat
    def list_participants():
        return [participant['name'] for participant in file_data['participants']]

    # Function to get all messages and organize it into usable data
    def get_all_messages():
        global total_call_duration_seconds, total_calls, actor_reactions # some global varaiables
        messages = file_data['messages']
        for message in messages:
            # to convert the timestamp into year, week, day, and hour
            day_of_year, time_of_day, day_of_week = convert_timestamp(message['timestamp_ms'])
            message['day_of_year'] = day_of_year
            message['time_of_day'] = time_of_day
            timestamp_ms = message.get('timestamp_ms', 0)
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)
            message['day_of_week'] = calendar.day_name[timestamp.weekday()]
            message['hour_of_day'] = timestamp.hour

            # Process call duration from video chats in Messenger
            call_duration = message.get('call_duration')
            if call_duration is not None:
                total_call_duration_seconds += call_duration
                total_calls += 1
                day_of_week = calendar.day_name[timestamp.weekday()]
                calls_duration_per_day_of_week[day_of_week] += call_duration
            
            # To figure out the emojis used in reactions in the chat
            reactions = message.get('reactions', [])
            for reaction in reactions:
                actor = reaction.get('actor')
                raw_emoji = reaction.get('reaction')
                decoded_emoji = decode_utf8_escapes(raw_emoji)
                actor_reactions[actor]['total_reactions'] += 1
                actor_reactions[actor]['emojis'][decoded_emoji] += 1

        return messages
    
    # Function to count messages sent by each participant 
    # INSERT PERSONAL DATA HERE
    def count_messages():
        message_count = {'FIRST NAME': 0, 'SECOND NAME': 0} # REPLACE FIRST NAME AND SECOND NAME WITH PARTICPANT NAMES
        for message in file_data['messages']:
            sender = message.get('sender_name')
            if sender in message_count:
                message_count[sender] += 1
        return message_count
    
     # Function to count top words sent by each participant
    def count_top_words():
        word_count = Counter()
        for message in file_data['messages']:
            # Extract the text from each message
            text = message.get('content', '').lower()
            # Tokenize the text into words (split on non-word characters)
            words = re.findall(r'\b\w+\b', text)
            word_count.update(words)
        return word_count
    
    # function to count a target word and its variations. For example: "you" also returns the count for "your" 
    def count_target_word_variations():
        word_count = 0
        for message in file_data['messages']:
            # Extract the text from each message
            text = message.get('content', '').lower()
            # Find all words
            words = re.findall(r'\b\w+\b', text)
            # Count occurrences of the target word and its variations
            word_count += sum(target_word in word for word in words)
        return word_count

    # Function to count emojis
    def count_all_emojis():
        all_emoji_count = Counter()
        for message in file_data['messages']:
            text = message.get('content', '')
            all_emoji_count.update(count_emojis(text))
        return all_emoji_count
    
    
    
    # returning the parsed information that we want to use
    return {
        'list_participants': list_participants,
        'get_all_messages': get_all_messages,
        'count_messages' : count_messages,
        'count_top_words': count_top_words,
        'count_target_word_variations': count_target_word_variations,
        'count_all_emojis': count_all_emojis,
    }

# a function testing the positivity/negativity of total messages sent 
def analyze_sentiment(messages):
    sentiment_score = 0
    for message in messages:
        text = message.get('content', '')
        blob = TextBlob(text)
        sentiment_score += blob.sentiment.polarity
    return sentiment_score / len(messages) if messages else 0

# BEGINNING OF MAIN FUNCTION
# Path where the JSON files are stored, adjust as necessary
# INSERT PERSONAL DATA HERE
path_to_json_files = 'FILEPATH' #REPLACE FILEPATH WITH A FILEPATH TO *.JSON FILES

# Lists to store aggregated participants and messages from all JSON files
all_participants = []
all_messages = []

# INSERT PERSONAL DATA HERE
message_count = {'FIRST NAME': 0, 'SECOND NAME': 0} # REPLACE FIRST NAME AND SECOND NAME WITH PARTICIPANTS
total_word_count = Counter()

# Dictionary to store reactions data
actor_reactions = defaultdict(lambda: {'total_reactions': 0, 'emojis': Counter()})

# Initialize the count for the target word
# INSERT PERSONAL DATA HERE
target_word = "TARGETWORD" # REPLACE TARGETWORD WITH ANY WORD YOU ARE TRYING TO FIND A COUNT FOR
target_word_count = 0

# New dictionaries for time-based analysis
day_of_week_count = defaultdict(int)
hour_of_day_count = defaultdict(int)

# Iterate over each JSON file and aggregate data
#INSERT PERSONAL DATA HERE
start_date = datetime('YEAR', 'MONTH', 'DAY', tzinfo=timezone.utc)  # REPLACE 'YEAR', 'MONTH', 'DAY', WITH NUMERICAL REPRESENTATIONS

# Initialize a Counter for emojis
total_emoji_count = Counter()

# New variables for call analysis
total_call_duration_seconds = 0
total_calls = 0
calls_duration_per_day_of_week = defaultdict(int)

# Iterate over each JSON file and aggregate data
for file_name in glob.glob(path_to_json_files): # if your file path includes multiple json files it aggregates it 
    with open(file_name, 'r') as file:
        file_data = json.load(file)
        file_data = filter_messages_by_date(file_data, start_date)
        chat_data = parse_json_chat(file_data, target_word)
        all_participants.extend(chat_data['list_participants']())
        all_messages.extend(chat_data['get_all_messages']())
        file_message_count = chat_data['count_messages']()

        # Update the overall message count
        for sender in file_message_count:
            message_count[sender] += file_message_count[sender]

        # Update word counts
        file_word_count = chat_data['count_top_words']()
        total_word_count.update(file_word_count)

        # target word
        target_chat_data = parse_json_chat(file_data, target_word)
        target_word_count += target_chat_data['count_target_word_variations']()

        #dates
        for message in chat_data['get_all_messages']():
            day_of_week_count[message['day_of_week']] += 1
            hour_of_day_count[message['hour_of_day']] += 1

        #emojis
        for message in file_data['messages']:
            text = message.get('content', '')
            decoded_text = decode_utf8_escapes(text)
            total_emoji_count.update(count_emojis(decoded_text))

# BEGINNING PRINT STATEMENTS 
# COMMENT AND UNCOMMENT THE FOLLOWING TO CHOOSE WHAT DATA TO PRINT 

# # Displaying participants and the first 5 messages for an overview
# participants = list(set(all_participants))  # Remove duplicates if needed
# messages = all_messages[:5]
# # print("Participants:", participants)
# # print("First 5 messages:", messages)
# print("Message counts:", message_count)

# # Get the top 30 words and their frequency
# top_30_words = total_word_count.most_common(30)
# print("Top 30 words:", top_30_words)

# # print the target word and its frequency
# print(f"Count of '{target_word}' and its variations:", target_word_count)

# # # After processing all messages
# # average_sentiment = analyze_sentiment(all_messages)
# # print("Average Sentiment Score:", average_sentiment)

# # Print the time-based analysis results
# print("Messages per Day of Week:", dict(day_of_week_count))
# print("Messages per Hour of Day:", dict(hour_of_day_count))

# # Get the top 10 emojis
# top_10_emojis = total_emoji_count.most_common(10)

# # Print the top 10 emojis and their counts
# print("Top 10 emojis:", top_10_emojis)

# # Printing a phrase frequency count 
# # INSERT PERSONAL DATA HERE
# phrase_to_search = "PHRASE" # REPLACE PHRASE WITH A PHRASE TO SEARCH. FOR EXAMPLE "I LOVE YOU"
# phrase_count = count_phrase_frequency(all_messages, phrase_to_search)
# print(f"The phrase '{phrase_to_search}' appears {phrase_count} times in the chat.")

# video calling data 
# # Convert total call duration to hours
# total_call_duration_hours = total_call_duration_seconds / 3600

# # Calculate average call duration in minutes
# average_call_duration = (total_call_duration_seconds / total_calls / 60) if total_calls > 0 else 0

# print(f"Total call duration in hours: {total_call_duration_hours:.2f} hours")
# print(f"Average call duration: {average_call_duration:.2f} minutes")
# print(f"Total number of calls: {total_calls}")
# for day, duration_seconds in calls_duration_per_day_of_week.items():
#     duration_hours = duration_seconds / 3600
#     print(f"Total call duration on {day}: {duration_hours:.2f} hours")

# # Emoji reaction data 
# for actor, data in actor_reactions.items():
#     print(f"Actor: {actor}")
#     print(f"Total reactions: {data['total_reactions']}")
#     top_3_emojis = data['emojis'].most_common(10)
#     print("Top 3 emojis:")
#     for emoji, count in top_3_emojis:
#         print(f"  Emoji: {emoji}, Frequency: {count}")
#     print()
