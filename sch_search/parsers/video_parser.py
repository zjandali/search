"""
{Description}
Download video (or get from cached), parse video and transcript, split into slides.
{License_info}
Scholarhub, Inc. 2021

"""

import os
import numpy as np
from skimage.transform import downscale_local_mean
import time
import skvideo.io
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from pytube import YouTube
import pandas as pd
from sch_search.weaviate.weaviate_calls import import_data

DOWNSCALE_FACTOR = 2
NORMALIZATION_WINDOW = 300
EPSILON = .01
THRESH = 2
BEGINNING_IGNORE = 1
CLOSE_IGNORE = 5
EVEN_SIZE = 300
SCENE_THRESHOLD = 5.0

class VideoSlideSplitter:

    def __init__(self, parser, split_method='slide'):
        ''' (Can change structure of class, add arguments later)
            parser: VideoParser
            split_method (optional): How the splits are determined. Options:
                'slide': Our custom method of attempting to
                detect where the slide changes,
                    using the constants defined in this file
                'even': Breaking the video into sections of
                length EVEN_SIZE seconds
                'scene': Using PySceneDetect to divide the video,
                with threshold SCENE_THRESHOLD
                'none': The whole video is treated as contiguous
        '''
        self.diffs = None
        if split_method == 'slide':
            self.splits = self.slide_splits(parser)
        elif split_method == 'none':
            self.splits = [0]
        elif split_method == 'even':
            self.splits = [i*EVEN_SIZE for i in range(parser.length//EVEN_SIZE)]
        else:
            self.splits = [0]
            print('Please choose a valid method of splitting the video.')
        self.sections = parser.get_text_from_sections(self.splits)

    def slide_splits(self, parser):
        ''' Returns a list of frames at which the movie changed
        '''
        start_time = time.time()

        # Iterate through the video to gather the mean squared difference over
        # pixels in the adjacent frames
        diffs = []
        percent_diff = []
        dots = []
        split_frames = []
        prev = parser.next_frame()
        curr = parser.next_frame()
        while curr is not None:
            diff = downscale_local_mean(curr, (DOWNSCALE_FACTOR, DOWNSCALE_FACTOR, 1)).\
                       astype(int) - downscale_local_mean(prev,
                                                          (DOWNSCALE_FACTOR, DOWNSCALE_FACTOR, 1)).\
                astype(int)
            diffs.append(np.mean(np.power(diff, 2)))
            prev = curr
            curr = parser.next_frame()

        # Within the window, gather statistics to normalize the differences
        stat_window = NORMALIZATION_WINDOW
        stat_frames = int(stat_window//parser.sec_per_frame)
        stdized_diffs = []
        num_included = min(len(diffs), stat_frames)
        relevant_diffs = diffs[:num_included]
        for i in range(len(diffs)):
            if i >= stat_frames//2 and i < len(diffs) - stat_frames//2:
                relevant_diffs.pop(0)
                relevant_diffs.append(diffs[i + stat_frames//2])
            mean_diffs = np.mean(relevant_diffs)
            std = np.sqrt(np.mean(np.power(np.array(relevant_diffs)-mean_diffs, 2)))
            std = max(std, EPSILON)
            stdized_diffs.append((diffs[i]-mean_diffs)/std)

        # Find splits where the normalized difference is above THRESH sigma
        splits = []
        split_frames = []
        for i in range(len(stdized_diffs)):
            if stdized_diffs[i] > THRESH:
                splits.append((i+1)*parser.sec_per_frame)
                split_frames.append(i+1)

        # Iterate backward through the splits and remove splits that are within
        # CLOSE_IGNORE seconds of each other
        idx = len(splits) - 1
        while idx > 0:
            if splits[idx] - splits[idx-1] < CLOSE_IGNORE:
                splits.pop(idx)
            idx -= 1

        # Remove any splits early in the video
        splits = [i for i in splits if i > BEGINNING_IGNORE]

        # Add a split at 0 since that is the beginning of the first section
        splits.insert(0, 0.0)

        # Store diffs for evaluation
        self.diffs = stdized_diffs

        return splits


    def get_text_from_scores(self, scores):
        ''' Returns the text from the section with the max score.
            scores: a list of len(self.sections) == len(self.splits)
        '''
        max_score_idx = np.argmax(scores)
        return self.sections[max_score_idx]


class VideoParser:
    def __init__(self, link, path, num_recent_frames=1, sample_frame_period=1,
                 force_download=False):
        ''' link: link to the YouTube video.
            path: path to the video if it has been downloaded already;
                otherwise, download the video to this path.
            num_recent_frames: the number of past frames to store before
                the current frame as we iterate through the video.
            sample_frame_period: an integer signifying how many frames to move forward
                every time a new frame is sampled.
        '''
        if not os.path.isdir(path) or len(os.listdir(path)) != 1 or force_download:
            self.download_video(link, path)
        self.video_path = os.path.join(path, os.listdir(path)[0])
        self.url = link
        self.num_recent_frames = num_recent_frames
        self.sample_frame_period = sample_frame_period
        self.reset_video_stream()

        metadata = skvideo.io.ffprobe(self.video_path)['video']
        self.length = metadata['@duration']

    def reset_video_stream(self, new_sample_frame_period=None):
        ''' Reset the video reader so that you can start reading in frames from the beginning again.
            May want to reset the sample_frame_period.
        '''
        self.buffer = []
        self.reader = skvideo.io.vreader(self.video_path)
        self.current_frame = -1
        if new_sample_frame_period:
            self.sample_frame_period = new_sample_frame_period
        metadata = skvideo.io.ffprobe(self.video_path)['video']
        self.sec_per_frame = float(metadata['@duration'])/float(metadata['@nb_frames']) \
                             * self.sample_frame_period


    def get_frame(self, frame_num):
        '''
        Return a frame by number if it is one of the recent frames stored in the buffer.
        '''
        if self.current_frame - frame_num >= self.num_recent_frames:
            print('Have not stored frame ' + frame_num)
            return
        if frame_num > self.current_frame:
            print('Have not reached frame ' + frame_num)
            return
        else:
            return self.buffer[frame_num - self.current_frame]

    def get_recent_frame(self, frames_ago):
        """
        Return a frame by how many frames back from the current frame it is.
        """
        if frames_ago > len(self.buffer):
            print('Have not stored frame ' + str(self.current_frame - frames_ago))
            return
        return self.buffer[-frames_ago]

    def next_frame(self):
        """
        Iterate self.sample_frame_period more frames through the video stream.
        Return the frame as a numpy array. If the movie is over return None.
        """
        self.current_frame += 1
        try:
            for _ in range(self.sample_frame_period):
                next_f = next(self.reader)
            self.buffer.append(next_f)
            if len(self.buffer) > self.num_recent_frames:
                    self.buffer.pop(0)
            return next_f
        except StopIteration:
            return None

    def get_current_time(self):
        return self.current_frame * self.sec_per_frame

    def download_video(self, link, SAVE_PATH='./video'):
        """
        Download the video to SAVE_PATH
        """
        yt = YouTube(link)
        d_video = yt.streams.first()
        d_video.download(SAVE_PATH)

    def get_transcript(self):
        """
        Return the dictionary of text of the video.
        """
        url_data = urlparse(self.url)
        query = parse_qs(url_data.query)
        video_id = query['v'][0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
        full_text = ' '.join([i['text'] for i in transcript])
        return transcript

    def get_text_from_sections(self, splits):
        """Returns a list of length len(splits) + 1 with a concatenated
            string of text for each section
        """
        transcript = self.get_transcript()
        results = []
        splits = splits[:]
        splits.append(transcript[-1]['start'] + transcript[-1]['duration'] + 1)
        i = 0
        while i < len(splits) - 1:
            text = ''
            if len(transcript) == 0:
                results.append('')
            else:
                while transcript and transcript[0]['start'] < splits[i+1]:
                    text += ' ' + transcript[0]['text']
                    transcript.pop(0)
            results.append(text)
            i += 1
        return results

def parse_video(client, links):
    df = pd.DataFrame(columns=['Document', 'Page', 'Paragraph', 'Text'])
    for link in links:
        # parser = VideoParser(link, os.path.dirname(os.path.realpath(__file__)) + "/videos/video0")
        # splitter = VideoSlideSplitter(parser)
        # sections = splitter.sections
        # new_df = pd.DataFrame({'Document': [link]*len(sections), 'Page': range(len(sections)), 'Paragraph': splitter.splits, 'Text': sections})
        new_df = pd.DataFrame({'Document': ['first link'], 'Page': [4], 'Paragraph': [2], 'Text': ['hello this is the video text']})
        df = df.append(new_df)
    import_data(client, df)
