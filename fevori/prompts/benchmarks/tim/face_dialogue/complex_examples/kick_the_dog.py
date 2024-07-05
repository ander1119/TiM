def execute_command(video, annotation, possible_answers, query)->[str, str, dict]
    # Trope: Kick the Dog
    # Definition: an act of cruelty by a character, typically towards a more vulnerable or defenseless entity, to establish the character's malevolence
    # Thought: we devide the trope detection into 4 steps
    # 1. Context Information Collection: To observe attacker's malevolence and victim's defenseless entity, we need to concern action and event in adjacent frames and use them as context to understand the story
    # 2. Event Observation: "Kick the Dog" would present in attack event within a frame. Use the context from first step as condition and query more detail in advance    
    # 3. Answer Selection: With information collected from second step, we leave the reasoning and question answering to select_answer api
    video_segment = VideoSegment(video, annotation)
    # Create a info dictionary, which would later pass to select_answer api
    info = {}
    # create an dict to record the frame indices that an unique person appear in 
    person_in_frame = {}
    for i, frame in enumerate(video_segment.frame_iterator()):
        # record the person id and the frame index that the person appear in
        for person in frame.find("person"):
            person_id = video_segment.face_identify(person)
            if person_id is None:
                continue
            if person_id not in person_in_frame:
                person_in_frame[person_id] = []
            person_in_frame[person_id].append(i)
        # check if there is any potential attack event with visual or dialogue information
        subtitles = " ".join(frame.get_subtitles())
        has_attack_event_in_visual = frame.simple_query(f"With subtitles '{subtitles}'. Is there any potential attack event in the scene?", to_yesno=True)
        has_attack_event_in_dialogue = frame.llm_query(f"With subtitles '{subtitles}'. Is there any potential attack event in the scene?", to_yesno=True)
        if 'yes' in has_attack_event_in_visual.lower() or 'yes' in has_attack_event_in_dialogue.lower():
            attack_event_info = {}
            attack_event_description = frame.simple_query(f"With subtitles '{subtitles}'. Please describe the attack event in 10 words")
            attack_event_info['description'] = attack_event_description
            for person in frame.find("person"):
                person_id = video_segment.face_identify(person)
                if person_id is None:
                    continue
                # query the person's description in local person cropped frame
                person_description = person.simple_query(f"Please describe his/her characteristics in 10 words")
                # check whether the person is the attacker in global frame
                is_attacker = frame.simple_query(f"Is person with '{person_description}' the attacker in the scene?", to_yesno=True)
                if 'yes' in is_attacker.lower():
                    # record the attacker information
                    attack_event_info['attacker_description'] = person_description
                    attack_event_info['attacker_id'] = person_id
                    attack_event_info['attack_reason'] = []
                    # query the reaction of the victim in global frame
                    attack_event_info['victim_reaction'] = frame.simple_query(f"With subtitles '{subtitles}'. Please describe the reaction of the victim in attack event '{attack_event_description}'")
                    # iterate the previous frames that the attacker appear in and query the reason why the attacker do the attack event in previous frames
                    for frame_index in person_in_frame[person_id].reverse():
                        previous_frame = video_segment.frame_from_index(frame_index)
                        previous_caption = " ".join(previous_frame.get_subtitles())
                        attack_reason = previous_frame.simple_query(f"With subtitles '{previous_caption}'. What's the reason that person with description '{person_description}' do '{attack_event_description}'?")
                        attack_event_info['attack_reason'].append(attack_reason)
            info[f"Attack event in {i} th frame"] = attack_event_info
    # Answer the query
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info