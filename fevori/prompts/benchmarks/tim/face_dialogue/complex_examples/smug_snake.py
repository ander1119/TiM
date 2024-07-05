def execute_command(video, annotation, possible_answers, query)->[str, str, dict]
    # Trope: Smug Snake
    # Definition: A type of character (usually a villain) who tends to treat friends and enemies alike with equal disdain, and whose overconfidence usually leads to their downfall.
    # Thought Process:
    # 1. Analyze character interactions in each frame for signs of disdain or smugness.
    # 2. Collect evidence of such behavior impacting their interactions negatively.
    # 3. Check for consistency of these traits across different scenes.

    video_segment = VideoSegment(video, annotation)
    info = {
        ""character infos"": {}
    }
    for i, frame in enumerate(video_segment.frame_iterator()):
        dialogue = "","".join(frame.get_subtitles())
        has_disdainful_talk = frame.llm_query(f""Does the dialogue '{dialogue}' suggest the character in frame being disdainful or smug to others?"", to_yesno=True)
        distain_talk = frame.llm_query(f""Why the dialogue '{dialogue}' suggest the character in frame being disdainful or smug to others?"", to_yesno=True)
        for person in frame.find(""person""):
            person_id = video_segment.face_identify(person)
            if person_id is None:
                for pid, character_infos in info[""character infos""].items():
                    description = character_infos[""description""]
                    is_same = person.simple_query(f""Is this person the same as {description}?"", to_yesno=True)
                    if ""yes"" in is_same.lower():
                        person_id = pid
                        break
            if person_id is None:
                continue
            # query the character's description and add into character_description
            if person_id not in info[""character infos""]:
                info[""character infos""][person_id] = {
                    ""description"": person.simple_query(""Please describe his/her appearance in 10 words""),
                    ""no distain action count"": 0,
                    ""distainful actions"": []
                }
            description = info[""character infos""][person_id][""description""]
            has_distainful_behavior = frame.simple_query(f""Does person in description '{description}' behave distainful or smug to others"", to_yesno=True)
            distainful_behavior = frame.simple_query(f""Why does person in description '{description}' behave distainful or smug to others"", to_yesno=True)
            if ""yes"" in has_distainful_behavior.lower():
                info[""character infos""][person_id][""distainful actions""].append(distainful_behavior)
            else:
                info[""character infos""][person_id][""no distain action count""] += 1
            if ""yes"" in has_disdainful_talk.lower():
                info[""character infos""][person_id][""distainful actions""].append(distain_talk)
            else:
                info[""character infos""][person_id][""no distain action count""] += 1
    # Use the collected information to answer the query
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info