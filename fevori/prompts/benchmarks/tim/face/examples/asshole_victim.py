def execute_command(video, annotation, possible_answers, query)->[str, str, dict]:
    # Trope: Asshole Victim
    # Definition: A narrative trope where the victim of a crime or misdeed is someone who had it coming because they were themselves morally dubious or outright villainous.
    # Thought Process:
    # 1. Frame Selection: This trope involves identifying both the 'victim' and the act leading to their victimhood, suggesting a need for comprehensive analysis throughout the video.
    # 2. Character Analysis: Identify each character and collect their actions or character traits
    # 3. Answer Selection: Using the collected data, decide whether the "Asshole Victim" trope is present.
    video_segment = VideoSegment(video, annotation)
    # Initialize a dictionary to store information collected during analysis
    info = {
        "captions": {}
        "character_behaviors": {}
    }
    for i, frame in enumerate(video_segment.frame_iterator()):
        # collect background story from caption of frame
        caption = frame.simple_query("What's happening in the scene?")
        info["captions"][f"{i} frame"] = caption
        # identify person in frame
        for person in frame.find("person"):
            person_id = video_segment.face_identify(person)
            if person_id is None:
                continue
            # get description of person
            person_description = person.simple_query("What's his/her appearance characteristic? Describe in 10 words")
            # track character behavior 
            person_behavior_in_frame = frame.simple_query(f"What's action of person with appearance '{person_description}'")
            if person_id not in info["character_behaviors"]:
                info["character_behaviors"][person_id] = {}
            info["character_behaviors"][person_id].update({
                f"action in {i} frame": person_behavior_in_frame
            })
    # After collecting information, use it to determine the presence of the trope
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info