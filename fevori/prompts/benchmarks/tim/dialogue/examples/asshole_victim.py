def execute_command(video, annotation, possible_answers, query)->[str, str, dict]:
    # Trope: Asshole Victim
    # Definition: A narrative trope where the victim of a crime or misdeed is someone who had it coming because they were themselves morally dubious or outright villainous.
    # Thought Process:
    # 1. Frame Selection: This trope involves identifying both the 'victim' and the act leading to their victimhood, suggesting a need for comprehensive analysis throughout the video.
    # 2. Character Analysis: Identify the 'victim' character and analyze their actions or character traits that justify the trope's criteria.
    # 3. Incident Analysis: Look for an incident within the video that cements the character's role as a victim.
    # 4. Morality Check: Determine if there's a narrative or visual cue indicating the victim's negative moral standing.
    # 5. Answer Selection: Using the collected data, decide whether the "Asshole Victim" trope is present.
    video_segment = VideoSegment(video, annotation)
    # Initialize a dictionary to store information collected during analysis
    info = {}
    for i, frame in enumerate(video_segment.frame_iterator()):
        # the trope usually present with human character, thus detect person first
        if frame.exists("person"):
            # use ImagePatch.get_subtitles() to get dialogue, latter use the dialogue with query as context information
            subtitles_info = "With subtitles '" + ' '.join(frame.get_subtitles()) + "'"
            incident_description = frame.simple_query(subtiltles_info + "Describe the incident happened in the image.")
            info[f"Character trait in {i}th frame"] = []
            info[f"Morality check in {i}th frame"] = []
            for person in frame.find("person"):
                # Analyze the character's actions or traits
                person_trait = person.simple_query(subtitles_info + "What is the person doing? What are his/her traits?")
                morality_query = person.simple_query(subtitles_info + "Does the he/she show negative moral traits?", to_yesno=True)
                # Store the collected information
                info[f"Character trait in {i}th frame"].append(person_trait)
                info[f"Morality check in {i}th frame"].append(morality_query)
            info[f"Incident description in {i}th frame"] = incident_description
    # After collecting information, use it to determine the presence of the trope
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info