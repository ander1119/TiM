def execute_command(video, annotation, possible_answers, query)->[str, str, dict]:
    # Trope: Big Bad
    # Definition: The character who is the direct cause of all of the bad happenings in a story.
    # Thought Process:
    # 1. Character Identification: Identify characters and track their actions across frames.
    # 2. Event Linking: Determine which negative events are directly caused by the actions of a character.
    # 3. Consistency Check: Check for consistency in the character’s negative influence over the story arc.
    video_segment = VideoSegment(video, annotation)
    # Initialize a dictionary to store information collected during analysis
    info = {
        ""happened bad events"": {},
        ""character infos"": {}
    }
    for i, frame in enumerate(video_segment.frame_iterator()):
        for person in frame.find(""person""):
            # identify the person in the frame
            person_id = video_segment.face_identify(person)
            if person_id is None:
                # in case face_identify fails
                for pid, character_infos in info[""character infos""].items():
                    description = character_infos[""description""]
                    is_same = person.simple_query(f""Is this person the same as {description}?"", to_yesno=True)
                    if ""yes"" in is_same.lower():
                        person_id = pid
                        break
            if person_id is None:
                continue
            # query the character""s description and add into character_description
            if person_id not in info[""character infos""]:
                info[""character infos""][person_id] = {
                    ""description"": person.simple_query(""Please describe his/her appearance in 10 words""),
                    ""actions"": {}
                }
            # query the character""s action in the frame
            action = person.simple_query(""Please describe his/her action in the scene"")
            info[""character infos""][person_id][""actions""][f""{i} frame""] = action
        # query the negative events happening in the scene
        event = frame.simple_query(""What's happening in the scene"")
        any_negative_event = frame.simple_query(""Is there any negative event happening in the scene?"", to_yesno=True)
        if ""yes"" in any_negative_event.lower():
            info[""happened bad events""][f""{i} frame""] = {
                ""event"": event,
                ""potential cause"": []
            }
            for pid, character_infos in info[""character infos""].items():
                # check if the character is a potential cause of the negative event
                character_description = character_infos[""description""]
                for prev_i in range(i, max(i-5, 0), -1):
                    prev_action = character_infos[""actions""].get(f""{prev_i} frame"", None)
                    if prev_action is not None:
                        is_person_potential = frame.simple_query(f""Is person with '{character_description}' a potential cause of '{event}'?"", to_yesno=True)
                        is_action_potential = frame.simple_query(f""Is action '{prev_action}' a potential cause of '{event}'?"", to_yesno=True)
                        if ""yes"" in is_person_potential.lower() or ""yes"" in is_action_potential:
                            info[""happened bad events""][f""{i} frame""][""potential cause""].append(pid)
                        break
    # After collecting information, use it to determine the presence of the trope
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info