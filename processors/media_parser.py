import os
import numpy as np
from skimage.transform import downscale_local_mean
import time
import skvideo.io
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from pytube import YouTube
import pandas as pd
from weaviate.weaviate_calls import import_data

DOWNSCALE_FACTOR = 2
NORMALIZATION_WINDOW = 300
MIN_STD = 0.01
SPLIT_THRESHOLD = 2
IGNORE_INITIAL_SECONDS = 1
IGNORE_CLOSE_SECONDS = 5
FIXED_SECTION_LENGTH = 300
SCENE_DETECTION_THRESHOLD = 5.0

class VideoSlideSeparator:
    def __init__(self, parser, method='slide'):
        """
        Initializes the VideoSlideSeparator with a specific splitting method.
        
        Args:
            parser: Instance of VideoParser.
            method (str): Method to determine splits. Options are 'slide', 'even', 'scene', or 'none'.
        """
        self.differences = None
        if method == 'slide':
            self.splits = self.detect_slide_changes(parser)
        elif method == 'none':
            self.splits = [0]
        elif method == 'even':
            self.splits = [i * FIXED_SECTION_LENGTH for i in range(parser.length // FIXED_SECTION_LENGTH)]
        else:
            self.splits = [0]
            print('Invalid splitting method selected.')
        self.sections = parser.extract_text_from_splits(self.splits)

    def detect_slide_changes(self, parser):
        """Identifies frame timestamps where slide changes occur."""
        start_time = time.time()
        differences = []
        used_diffs = []
        frames = []
        split_times = []
        previous_frame = parser.get_next_frame()
        current_frame = parser.get_next_frame()
        
        while current_frame is not None:
            diff = downscale_local_mean(current_frame, 
                                        (DOWNSCALE_FACTOR, DOWNSCALE_FACTOR, 1)).astype(int) - \
                   downscale_local_mean(previous_frame, 
                                        (DOWNSCALE_FACTOR, DOWNSCALE_FACTOR, 1)).astype(int)
            differences.append(np.mean(np.power(diff, 2)))
            previous_frame = current_frame
            current_frame = parser.get_next_frame()

        window_size = NORMALIZATION_WINDOW
        window_frames = int(window_size // parser.seconds_per_frame)
        standardized_diffs = []
        active_diffs = differences[:min(len(differences), window_frames)]
        
        for i in range(len(differences)):
            if window_frames // 2 <= i < len(differences) - window_frames // 2:
                active_diffs.pop(0)
                active_diffs.append(differences[i + window_frames // 2])
            mean_diff = np.mean(active_diffs)
            std_dev = max(np.sqrt(np.mean((np.array(active_diffs) - mean_diff) ** 2)), MIN_STD)
            standardized_diffs.append((differences[i] - mean_diff) / std_dev)

        potential_splits = []
        split_frames_list = []
        for i, std_diff in enumerate(standardized_diffs):
            if std_diff > SPLIT_THRESHOLD:
                potential_splits.append((i + 1) * parser.seconds_per_frame)
                split_frames_list.append(i + 1)

        # Remove splits that are too close to each other
        index = len(potential_splits) - 1
        while index > 0:
            if potential_splits[index] - potential_splits[index - 1] < IGNORE_CLOSE_SECONDS:
                potential_splits.pop(index)
            index -= 1

        # Exclude early splits
        filtered_splits = [t for t in potential_splits if t > IGNORE_INITIAL_SECONDS]
        filtered_splits.insert(0, 0.0)  # Add the start time
        self.differences = standardized_diffs

        return filtered_splits

class VideoParser:
    def __init__(self, url, save_path, recent_frames=1, frame_period=1, force_download=False):
        """
        Initializes the VideoParser with video details.
        
        Args:
            url: URL of the YouTube video.
            save_path: Directory path to save the video.
            recent_frames (int): Number of recent frames to retain.
            frame_period (int): Number of frames to skip between samples.
            force_download (bool): Whether to force re-download the video.
        """
        if not os.path.isdir(save_path) or len(os.listdir(save_path)) != 1 or force_download:
            self.retrieve_video(url, save_path)
        self.video_path = os.path.join(save_path, os.listdir(save_path)[0])
        self.url = url
        self.recent_frame_count = recent_frames
        self.frame_skip_period = frame_period
        self.reset_stream()
        
        metadata = skvideo.io.ffprobe(self.video_path)['video']
        self.duration = float(metadata['@duration'])

    def reset_stream(self, new_frame_period=None):
        """Resets the video reader to start from the beginning."""
        self.buffer = []
        self.reader = skvideo.io.vreader(self.video_path)
        self.current_frame_index = -1
        if new_frame_period:
            self.frame_skip_period = new_frame_period
        metadata = skvideo.io.ffprobe(self.video_path)['video']
        self.seconds_per_frame = float(metadata['@duration']) / float(metadata['@nb_frames']) * self.frame_skip_period

    def get_specific_frame(self, frame_number):
        """
        Retrieves a specific frame if it's within the recent buffer.
        
        Args:
            frame_number (int): The frame number to retrieve.
        
        Returns:
            The requested frame as a numpy array or None if unavailable.
        """
        if self.current_frame_index - frame_number >= self.recent_frame_count:
            print(f'Frame {frame_number} not available in buffer.')
            return None
        if frame_number > self.current_frame_index:
            print(f'Frame {frame_number} has not been reached yet.')
            return None
        return self.buffer[frame_number - self.current_frame_index]

    def get_recent_frame(self, frames_back):
        """
        Retrieves a frame from a specified number of frames ago.
        
        Args:
            frames_back (int): Number of frames back from the current frame.
        
        Returns:
            The requested frame as a numpy array or None if unavailable.
        """
        if frames_back > len(self.buffer):
            print(f'Frame {self.current_frame_index - frames_back} not stored in buffer.')
            return None
        return self.buffer[-frames_back]

    def get_next_frame(self):
        """
        Advances the video stream and retrieves the next frame.
        
        Returns:
            The next frame as a numpy array or None if the video has ended.
        """
        self.current_frame_index += 1
        try:
            for _ in range(self.frame_skip_period):
                next_frame = next(self.reader)
            self.buffer.append(next_frame)
            if len(self.buffer) > self.recent_frame_count:
                self.buffer.pop(0)
            return next_frame
        except StopIteration:
            return None

    def current_time(self):
        """Returns the current timestamp based on the frame index."""
        return self.current_frame_index * self.seconds_per_frame

    def retrieve_video(self, url, destination='./videos'):
        """
        Downloads the YouTube video to the specified directory.
        
        Args:
            url: YouTube video URL.
            destination (str): Directory path to save the video.
        """
        yt = YouTube(url)
        video_stream = yt.streams.first()
        video_stream.download(destination)

    def fetch_transcript(self):
        """Retrieves the transcript of the YouTube video."""
        parsed_url = urlparse(self.url)
        query_params = parse_qs(parsed_url.query)
        video_id = query_params['v'][0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript

    def extract_text_from_splits(self, splits):
        """
        Extracts text segments based on the provided split timestamps.
        
        Args:
            splits (list): List of timestamps indicating split points.
        
        Returns:
            List of text segments corresponding to each split.
        """
        transcript = self.fetch_transcript()
        results = []
        splits = splits[:]
        splits.append(transcript[-1]['start'] + transcript[-1]['duration'] + 1)
        index = 0
        while index < len(splits) - 1:
            text_segment = ''
            if not transcript:
                results.append('')
            else:
                while transcript and transcript[0]['start'] < splits[index + 1]:
                    text_segment += ' ' + transcript.pop(0)['text']
            results.append(text_segment)
            index += 1
        return results

def process_video(client, video_links):
    """
    Processes a list of video links and uploads their parsed data to Weaviate.
    
    Args:
        client: Weaviate client instance for database operations.
        video_links (list): List of YouTube video URLs.
    
    Returns:
        None
    """
    dataframe = pd.DataFrame(columns=['Document', 'Page', 'Paragraph', 'Text'])
    for link in video_links:
        # Example data; replace with actual parsing logic
        new_data = pd.DataFrame({
            'Document': ['first_video_link'],
            'Page': [4],
            'Paragraph': [2],
            'Text': ['hello this is the video text']
        })
        dataframe = dataframe.append(new_data, ignore_index=True)
    import_data(client, dataframe)