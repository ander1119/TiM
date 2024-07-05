def execute_command(video, annotation, possible_answers, query)->[str, str, dict]
    # Trope: Downer Ending
    # Definition: an ending that is sad, tragic, or otherwise less positive than the audience might have expected, often leaving the protagonist or key characters in a worse state than they were at the beginning or facing significant loss
    # Thought: we devide the trope detection into 3 steps
    # 1. Frame selection: "Downer Ending" refers to an ending, so we only analyze the final part of video segment
    # 2. Detection of emotional and contextual cues: Analyze the frames for visual cues of sadness, loss, or tragedy. This could involve detecting specific objects, settings, or facial expressions associated with negative outcomes
    # 3. Answer Selection: Use select_answer api to select the most possible answer with previously collected information 
    video_segment = VideoSegment(video, annotation)
    # Assuming the last 10% of the video is a reasonable segment to analyze for the ending
    ending_segment_start = int(video_segment.num_frames * 0.9)
    ending_segment = video_segment.trim(start=ending_segment_start)
    # Create a info dictionary
    info = {
        "Total number of frames": video_segment.num_frames
    }
    for i, frame in enumerate(ending_segment.frame_iterator()):
        # use ImagePatch.get_subtitles() to get dialogue, latter use the dialogue with query as context information
        subtitles_info = "Consider subtitles in frame: '" + ' '.join(frame.get_subtitles()) + "'"
        # Detect visual cues of sadness, tragedy, or loss
        has_sadness = frame.simple_query(subtitles_info + "Is there sadness or mourning?", to_yesno=True)
        has_tragedy = frame.simple_query(subtitles_info + "Is there visible tragedy or destruction?" to_yesno=True)

        if "yes" in sadness_query.lower() or "yes" in tragedy_query.lower():
            # Caption the frame
            caption = frame.simple_query(subtitles_info + "What is in the frame?")
            sadness_query = frame.simple_query(subtitles_info + "What sadness or mourning event is in the frame?")
            tragedy_query = frame.simple_query(subtitles_info + "What visible tragedy or destruction event is in the frame?")
            info[f"Caption of {ending_segment.start + 1} th frame"] = caption
            info[f"Sadness or mourning event in {ending_segment.start + 1} th frame"] = sadness_query
            info[f"Visible tragedy or destruction event in {ending_segment.start + 1} th frame"] = tragedy_query
    # Answer the query
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info