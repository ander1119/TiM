def execute_command(video, annotation, possible_answers, query):
    # Trope: Big Bad
    # Definition: The character who is the direct cause of all of the bad happenings in a story.
    # Thought Process:
    # 1. Frame Selection: Analyze each frame to identify key characters and their actions.
    # 2. Character Analysis: Identify the main antagonist and their actions throughout the video.
    # 3. Answer Selection: Determine if there is a single character causing most of the negative events.

    video_segment = VideoSegment(video, annotation)
    info = {
        "character_actions": {},
        "negative_impacts": {}
    }
    for i, frame in enumerate(video_segment.frame_iterator()):
        # Identify all characters in the frame
        for character in frame.find("person"):
            character_id = video_segment.face_identify(character)
            if character_id is None:
                continue
            # Query the action of the character in the frame
            action_query = frame.simple_query("What is this person doing?")
            # Check if the action has a negative impact
            negative_query = f"Does the action '{action_query}' have a negative impact?"
            has_negative_impact = frame.llm_query(negative_query, to_yesno=True)
            # Store character actions and their impacts
            if character_id not in info["character_actions"]:
                info["character_actions"][character_id] = []
            info["character_actions"][character_id].append(action_query)
            if "yes" in has_negative_impact.lower():
                if character_id not in info["negative_impacts"]:
                    info["negative_impacts"][character_id] = 0
                info["negative_impacts"][character_id] += 1

    # After collecting information, use it to determine the presence of the trope
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info