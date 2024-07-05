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
    for i, frame in enumerate(video_segment.frame_iterator()):
        # understanding current frame with context information
        caption_query = "What is happening in the scene? please answer with at least 10 words"
        caption = frame.simple_query(caption_query)
        # check if there is any potential attack event
        has_attack_event = frame.llm_query(f"Is there any potential attack event in description '{caption}'?", to_yesno=True)
        if 'yes' in has_attack_event.lower():
            # query the event in detail
            attack_event_query = "What attack event is in the scene and what action and emotion does attacker and victim have, please answer with at least 40 words"     
            attack_event_description = frame.simple_query(attack_event_query)
            info[f"Attack event in {i} th frame"] = attack_event_description
    # Answer the query
    answer, reason = video_segment.select_answer(info, query, possible_answers)
    return answer, reason, info