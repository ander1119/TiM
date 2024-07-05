def execute_command(video, annotation, possible_answers, query)->[str, str, dict]:
    # Trope: Love at First Sight
    # Definition: An instance where two characters meet for the first time and immediately fall in love, often leading to significant plot developments.
    # Thought: The trope detection involves three steps:
    # 1. Frame Selection: Iterate through each frame to find when the two characters first meet.
    # 2. Emotional and Contextual Analysis: Analyze the frames for visual cues of love at first sight. This involves detecting facial expressions, body language, and any other indications of immediate romantic interest.
    # 3. Answer Selection: Use select_answer API to choose the most likely answer based on the collected information.
    video_segment = VideoSegment(video, annotation)
    info = {}
    for i, frame in enumerate(video_segment.frame_iterator()):
        # use ImagePatch.get_subtitles() to get dialogue, latter use the dialogue with query as context information
        subtitles_info = "With subtitles '" + " ".join(frame.get_subtitles()) + "'"
        for character in frame.find("person"):
            character_id = video_segment.face_identify(character)
            if character_id is None:
                continue
            character_action = character.simple_query(subtiltles_info + "What's he/she doing?")
            character_emotion = character.simple_query(subtiltles_info + "What's his/her emotion?")
            if character_id not in info:
                character_info[character_id] = {}
            info[character_id].update({
                f"Action in {i} frame": character_action,
                f"Emotion in {i} frame": character_emotion
            })
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info