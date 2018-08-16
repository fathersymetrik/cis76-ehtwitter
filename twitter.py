#!/usr/bin/python3
# Jesse Warren
# 1.3.45D

from re import finditer, search; # create an iterable container of regex matches
from argparse import ArgumentParser;

from random import choice, randint;
from time import sleep;
import tweepy;

# define argument parameters here
arg_params = [
    ('source', 'specifies the twitter account to read tweets from'),
    ('replies', 'specifies which .txt file to choose replies from'),
    ('comments', 'specifies which .txt file to choose comments from'),
];

intro_string = '';

# allow several command line arguments in case users have custom txt files
t_parser = ArgumentParser();
for item in arg_params:
    t_parser.add_argument('-{0}'.format(item[0][0]), '--{0}'.format(item[0]), help=item[1]);
    intro_string += ' | -{0} {1}'.format(item[0][0], item[0])
t_args = t_parser.parse_args();

print('Welcome to the twitter bot for EH CIS 76.\n{0}'.format(intro_string));
print('[DEBUG NOTE] I am using a version of Tweepy that does not seem to support 280 character tweets. Please be aware of this and check for updates!\n');

class create_core():
    def __init__(self, tweepy, t_args):
    # decoded strings because 'buffer interface' errors on opus
    # get your own!
        self.consumer_key = 'Y ... g';
        self.consumer_secret = 'D ... O';
        self.access_token = '9 ... o';
        self.access_secret = 'b ... g';

    # time in seconds to wait between checking for new tweets.
        self.seconds_before_input = 10;

    # authentication to the API
        self.first_authentication_protocol = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret);
        self.first_authentication_protocol.set_access_token(self.access_token, self.access_secret);
        self.API_access = tweepy.API(self.first_authentication_protocol);

    # empty __init__ variables
        self.latest_tweets = [];
        self.check_keywords = {};
        self.keywords_found = {};
        self.recent_tweets = {};
        self.listening_to = None;
        self.comments = None;
        self.replies = None;

        self.arg_list = {
            'replies':[self.replies, t_args.replies, 'random-replies.txt'],
            'comments':[self.comments, t_args.comments, 'nine-bakers-dozen.txt'],
            'source':[self.listening_to, t_args.source, 'TARGET_HERE']
        };

    # if -s not specified, uses the default username
        self.listening_to = self.try_except(self.argument_formatting, 'source');

    # checks for -c and -r arguments
        self.comments = self.try_except(self.argument_formatting, 'comments');
        self.nine_bakers_dozen = open(self.comments, 'r').read().split('\n')[:-1];

        self.replies = self.try_except(self.argument_formatting, 'replies');
        self.random_replies = open(self.replies, 'r').read().split('\n')[:-1];

    # opens data files and creates the required dictionaries
        self.recent_tweets = self.try_except(self.file_formatting, 'recent-tweets.txt');
        self.watch_words = self.try_except(self.file_formatting, 'watch-words.txt');

    # this is the list of commands and passed string
        self.command_list = {
            'reply':(self.random_replies, '__SOURCE__ __REPLY CHOICE__'),
            'comment':(self.nine_bakers_dozen, '__REPLY CHOICE__ __TWEET LINK__'),
            'retweet':(None, '__TWEET__'),
        };

    def argument_formatting(self, string_arg):
        # using the dict above, uses the default arg unless an arg is specified.
        if not self.arg_list[string_arg][1]:
            self.arg_list[string_arg][0] = self.arg_list[string_arg][2];
        else:
            self.arg_list[string_arg][0] = self.arg_list[string_arg][1];
        return(self.arg_list[string_arg][0]);

    def file_formatting(self, file_choice):
        # creates a dict from files with a 'key:value' syntax per line
        temp_file = open(file_choice, 'r').read().split('\n')[:-1];
        temp_file = [(i.split(':')[0], i.split(':')[1]) for i in temp_file];
        temp_file = {key:value for (key, value) in temp_file};
        return(temp_file);

    def is_tweetable(self, tweet_checking):
        # determines if a message is tweetable
        link_finding_regex = r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)';
        links_found = finditer(link_finding_regex, tweet_checking);
        for current_link in links_found:
            # twitter replaces all links with a t.co shortened URL that is 23 characters long
            tweet_checking = tweet_checking.replace(str(current_link.group(0)), 'twenty three characters');
        if len(tweet_checking) <= 280: # twitter now allows tweets up to 280 characters long
            return(True);
        return(False);

    def listen_to_source(self):
        # grabs the latest (20?) tweets from the sources timeline and creates an ID:Tweet dictinary
        self.latest_tweets = self.API_access.user_timeline(self.listening_to);
        self.latest_tweets = [(i.id, i.text) for i in self.latest_tweets];
        self.latest_tweets = {str(key):value for (key, value) in self.latest_tweets};
        return(True);

    def find_new_tweets(self):
        # locates tweets that haven't been seen before (ID does not exist in recent-tweets.txt)
        for t_id in [l_id for l_id in self.latest_tweets]:
            if t_id not in [r_id for r_id in self.recent_tweets]:
                self.check_keywords[t_id] = self.latest_tweets[t_id];
        if len(self.check_keywords) < 1:
            return(False);
        return(True);

    def check_for_keywords(self):
        # scans new tweets for any relevant regex keywords
        for tweet in self.check_keywords:
            for keyword in self.watch_words:
                if search(keyword, self.check_keywords[tweet]):
                    self.keywords_found[tweet] = (self.check_keywords[tweet], self.watch_words[keyword]);
            self.recent_tweets[tweet] = self.check_keywords[tweet];
        if len(self.keywords_found) < 1:
            return(False);
        return(True);

    def try_except(self, function, args=None):
        # general error handling, all functions are run through this
        try:
            if not args:
                return(function());
            else:
                return(function(args));
        except Exception as e:
            print('[DEBUG ACTIVE] Returning False in {0} to keep things running, but {1}'.format(function.__name__, e));
            return(False);

    def run_command(self, t_id):
        # determines which command to run, based on which keywords were found.
        tweet_command = self.keywords_found[t_id][1];
        tweet_message = self.keywords_found[t_id][0];
        if not self.command_list[tweet_command][0]:
            reply_choice = 'None';
        else:
            reply_choice = choice([reply for reply in self.command_list[tweet_command][0]]);

        command_syntax = {
            '__SOURCE__':'@{0}'.format(self.listening_to),
            '__REPLY CHOICE__':reply_choice,
            '__TWEET LINK__':'https://twitter.com/{0}/status/{1}'.format(self.listening_to[1:], t_id),
            '__TWEET__':tweet_message,
        };

        formatted_message = self.command_list[tweet_command][1];
        if tweet_command in self.command_list:
            for syntax in command_syntax:
                formatted_message = formatted_message.replace(syntax, command_syntax[syntax]);
            if self.try_except(self.is_tweetable, formatted_message):
                self.API_access.update_status(formatted_message);
                print('[TWEET SENT] I tweeted "{0}"'.format(formatted_message));
            else:
                print('[TWEET FAILED] I could not send that tweet.');
        else:
            print('[DEBUG ACTIVE] I received a command that I am not coded for yet.')
            return(False);
        return(True);

twitter_bug = create_core(tweepy, t_args);

# this probably doesn't slow things down, but just in case
if len(twitter_bug.watch_words) >= 15:
    print('[DEBUG NOTE] Too many keywords may slow me down!\n');

twitter_bug.try_except(twitter_bug.listen_to_source);

if twitter_bug.try_except(twitter_bug.find_new_tweets):
    # sets keywords_found to the tweets that contain keywords and are new
    twitter_bug.try_except(twitter_bug.check_for_keywords);
    current_counter = len(twitter_bug.keywords_found);
    for t_id in twitter_bug.keywords_found:
        twitter_bug.try_except(twitter_bug.run_command, t_id);

        # if this isn't the last (or only) event, it sleeps for a bit
        if current_counter > 1:
            sleep(twitter_bug.seconds_before_input);
            current_counter -= 1;

    # after all commands are run, it updates recent-tweets.txt
    recent_tweets_write = open('recent-tweets.txt', 'w');
    for t_id in twitter_bug.recent_tweets:
        recent_tweets_write.write('{0}:{1}\n'.format(t_id, twitter_bug.recent_tweets[t_id]));
    recent_tweets_write.close();
else:
    print('[DEBUG ACTIVE] No new tweets found.');

print('Thanks for running me! I am going to quit now, but run me again anytime you want to check for new tweets.');
