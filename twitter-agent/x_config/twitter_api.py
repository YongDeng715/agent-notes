from TwitterAPI import (TwitterAPI, TwitterOAuth, TwitterRequestError, 
	TwitterConnectionError, TwitterPager, HydrateType)


# NOTE: If any of the conversation is over a week old then it will not get 
# returned unless you are using academic credentials.
CONVERSATION_ID = '1889219750527741984'

"""
consumer_key=XC1VplLRpOlinhSw7LdGZ72CX
consumer_secret=MM8Ojtp8cgujiTT7Kmkq5hD7DoO6Hc9BwXxbVtRVbBiYzVLFsZ
bearer_token=AAAAAAAAAAAAAAAAAAAAAFii0wEAAAAAMDbIZiK4KJ0ldyNJR4cjpG0SGXU%3DHIocLZeBbfHMnMSq1luRzjTRxxNK32bSIc1JmXJj4NveNTH2yE
access_token_key=1707070880260698112-fVBL4GRp8GJa1GBlV8X2iM02jiDfcZ
access_token_secret=e5mdsJvfrcGA2SV6JfvrYsv380CgV5sOhKmoZOGJN69Ak
client_id=dnQzM2tuN3dfMU05UnJJOUJTU0M6MTpjaQ
client_secret=tdGJ8xSD-G-Akg5z5lJhIE4hR9XMS2_3wWMFal92rJobcnNrxl
"""

#
# UTILITY CLASS
#

class XTreeNode:
	"""XTreeNode is used to organize tweets as a tree structure"""

	def __init__(self, data):
		"""data is a tweet's json object"""
		self.data = data
		self.children = []
		self.replied_to_tweet = None
		if 'referenced_tweets' in self.data:
			for tweet in self.data['referenced_tweets']: 
				if tweet['type'] == 'replied_to':
					self.replied_to_tweet = tweet['id']
					break

	def id(self):
		"""a node is identified by its tweet id"""
		return self.data['id']

	def parent(self):
		"""the reply-to tweet is the parent of the node"""
		return self.replied_to_tweet

	def find_parent_of(self, node):
		"""append a node to the children of it's parent tweet"""
		if node.parent() == self.id():
			self.children.append(node)
			return True
		for child in self.children:
			if child.find_parent_of(node):
				return True
		return False

	def print_tree(self, level):
		"""level 0 is the root node, then incremented for subsequent generations"""
		created_at = self.data['created_at']
		username = self.data['author_id']['username']
		text_80chars = self.data['text'][0:80].replace('\n', ' ')
		print(f'{level*"_"}{level}: [{created_at}][{username}] {text_80chars}')
		level += 1
		for child in reversed(self.children):
			child.print_tree(level)


#
# PROGRAM BEGINS HERE
#

def init_twitter():
    """Initialize Twitter API connection"""
    try:
        o = TwitterOAuth.read_file("credentials.txt")
        api = TwitterAPI(
            # App-level credentials
            o.consumer_key,
            o.consumer_secret,
            # User-level tokens (必须传入)
            o.access_token_key,
            o.access_token_secret,
            auth_type='oAuth1', # 关键：使用 OAuth 1.0a
            api_version='2'
        )
        return api
    except Exception as e:
        print(f"Error initializing Twitter API: {e}")
        return None

def search_tweet(api, conversation_id):
    """Search tweets in a conversation thread"""
    try:
        # Get root tweet
        r = api.request(f'tweets/:{conversation_id}',
            {
                'expansions':'author_id',
                'tweet.fields':'author_id,conversation_id,created_at,referenced_tweets'
            },
            hydrate_type=HydrateType.REPLACE)

        root = None
        for item in r:
            root = XTreeNode(item)
            print(f'ROOT {root.id()}')
        if not root:
            print(f'Conversation ID {conversation_id} does not exist')
            return None

	# GET ALL REPLIES IN CONVERSATION
	# (RETURNED IN REVERSE CHRONOLOGICAL ORDER)
        # Get all replies
        pager = TwitterPager(api, 'tweets/search/recent', 
            {
                'query':f'conversation_id:{conversation_id}',
                'expansions':'author_id',
                'tweet.fields':'author_id,conversation_id,created_at,referenced_tweets'
            },
            hydrate_type=HydrateType.REPLACE)

    # "wait=2" means wait 2 seconds between each request.
    # The rate limit is 450 requests per 15 minutes, or 1 request every 15*60/450 = 2 seconds.
        orphans = []
        for item in pager.get_iterator(wait=2):
            node = XTreeNode(item)
            print(f'{node.id()} => {node.parent()}', item['author_id']['username'])
            orphans = [orphan for orphan in orphans if not node.find_parent_of(orphan)]
            if not root.find_parent_of(node):
                orphans.append(node)

        print('\nTREE...')
        root.print_tree(0)
	
	# YOU MIGHT GET ORPHANS WHEN PART OF THE CONVERSATION IS OLDER THAN A WEEK
        if len(orphans) > 0:
            print(f'Warning: {len(orphans)} orphaned tweets found')
            
        return root

    except TwitterRequestError as e:
        print(e.status_code)
        for msg in iter(e):
            print(msg)
        return None
    except TwitterConnectionError as e:
        print(e)
        return None
    except Exception as e:
        print(e)
        return None

def post_tweet(api, text):
    """Post a new tweet"""
    try:
        r = api.request('tweets', {'text': text}, method_override='POST')
        
        if r.status_code != 201:
            raise TwitterRequestError(r.status_code, r.text)

        data = r.json().get('data', {})
        tweet_id = data.get('id')
        print(f"Tweet posted successfully! Tweet ID: {tweet_id}")
        return tweet_id
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return None

if __name__ == "__main__":
    # Initialize Twitter API
    api = init_twitter()
    if not api:
        print("Failed to initialize Twitter API")
        exit(1)
        
    # Test search functionality
    print("\nTesting tweet search...")
    search_tweet(api, conversation_id=CONVERSATION_ID)
    
    # Test posting functionality
    print("\nTesting tweet posting...")
    test_tweet = "Hello Twitter! This is a test tweet from my Python script. #Python #TwitterAPI"
    tweet_id = post_tweet(api, test_tweet)
    if tweet_id:
        print(f"Successfully posted tweet with ID: {tweet_id}")