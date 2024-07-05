import numpy as np
import pandas as pd
import os
import argparse
import json
from sklearn.metrics import precision_recall_fscore_support

trope_2_cat = {'Big Bad': 'Character Trait', 'Jerkass': 'Character Trait', 'Faux Affably Evil': 'Character Trait', 'Smug Snake': 'Character Trait', 'Abusive Parents': 'Character Trait', 'Would Hurt a Child': 'Character Trait', 'Action Girl': 'Character Trait', 'Reasonable Authority Figure': 'Character Trait', 'Papa Wolf': 'Character Trait', 'Deadpan Snarker': 'Character Trait', 'Determinator': 'Character Trait', 'Only Sane Man': 'Character Trait', 'Anti-Hero': 'Character Trait', 'Asshole Victim': 'Character Trait', 'Jerk with a Heart of Gold': 'Character Trait', 'Even Evil Has Standards': 'Character Trait', 'Affably Evil': 'Character Trait', 'Too Dumb to Live': 'Character Trait', 'Butt-Monkey': 'Character Trait', 'Ax-Crazy': 'Character Trait', 'Adorkable': 'Character Trait', 'Berserk Button': 'Character Trait', 'Ms. Fanservice': 'Character Trait', 'The Alcoholic': 'Character Trait', 'Disappeared Dad': 'Character Trait', 'Would Hit a Girl': 'Character Trait', 'Oh, Crap!': 'Role Interaction', 'Driven to Suicide': 'Role Interaction', 'Adult Fear': 'Role Interaction', 'Not So Different': 'Role Interaction', 'Heroic BSoD': 'Role Interaction', 'Big \\"NO!\\"': 'Role Interaction', 'Eye Scream': 'Role Interaction', 'Gory Discretion Shot': 'Role Interaction', 'Impaled with Extreme Prejudice': 'Role Interaction', 'Off with His Head!': 'Role Interaction', 'Disney Villain Death': 'Role Interaction', 'Your Cheating Heart': 'Role Interaction', '\\"The Reason You Suck\\" Speech': 'Role Interaction', 'Tempting Fate': 'Role Interaction', 'Disproportionate Retribution': 'Role Interaction', 'Badass Boast': 'Role Interaction', 'Groin Attack': 'Role Interaction', 'Roaring Rampage of Revenge': 'Role Interaction', 'Big Damn Heroes': 'Role Interaction', 'Heroic Sacrifice': 'Role Interaction', "Screw This, I'm Outta Here!": 'Role Interaction', 'Kick the Dog': 'Role Interaction', 'Pet the Dog': 'Role Interaction', 'Villainous Breakdown': 'Role Interaction', 'Precision F-Strike': 'Role Interaction', 'Cluster F-Bomb': 'Role Interaction', 'Jerkass Has a Point': 'Role Interaction', 'Idiot Ball': 'Role Interaction', 'Batman Gambit': 'Role Interaction', 'Police are Useless': 'Situation', 'The Dragon': 'Situation', 'Cool Car': 'Situation', 'Body Horror': 'Situation', 'The Reveal': 'Situation', 'Curb-Stomp Battle': 'Situation', 'Cassandra Truth': 'Situation', 'Blatant Lies': 'Situation', 'Crapsack World': 'Situation', 'Comically Missing the Point': 'Situation', 'Fanservice': 'Situation', 'Fan Disservice': 'Situation', 'Brick Joke': 'Situation', 'Hypocritical Humor': 'Situation', 'Does This Remind You of Anything?': 'Situation', 'Black Comedy': 'Situation', 'Irony': 'Situation', 'Exact Words': 'Situation', 'Stealth Pun': 'Situation', 'Bittersweet Ending': 'Story Line', 'Karma Houdini': 'Story Line', 'Downer Ending': 'Story Line', 'Laser-Guided Karma': 'Story Line', 'Earn Your Happy Ending': 'Story Line', 'Karmic Death': 'Story Line', 'Nice Job Breaking It, Hero!': 'Story Line', 'My God, What Have I Done?': 'Story Line', 'What the Hell, Hero?': 'Story Line', 'Hope Spot': 'Story Line', 'Heel Face Turn': 'Story Line', 'Took a Level in Badass': 'Story Line', "Chekhov's Gun": 'Story Line', 'Foreshadowing': 'Story Line', "Chekhov's Skill": 'Story Line', "Chekhov's Gunman": 'Story Line', 'Red Herring': 'Story Line', 'Ironic Echo': 'Story Line', 'Hoist by His Own Petard': 'Story Line', 'Meaningful Echo': 'Story Line', 'Freudian Excuse': 'Story Line'}

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=str, help="Path to the folder containing results")
    parser.add_argument('--result_type', type=str, default='csv', help="Type of the result file")
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    if os.path.isfile(args.result):
        results = [args.result]
    else:
        results = [os.path.join(args.result, file) for file in os.listdir(args.result) if file.endswith(f'.{args.result_type}')]
    
    if args.result_type == 'json':
        json_results = []
        for result in results:
            json_results.extend(json.load(open(result, 'r')))
        answers = [x['answer'] for x in json_results]
        groundtruths = [x['groundtruth'] for x in json_results]
        tropes = [x['trope'] for x in json_results]
    else:
        dataframes = []
        for file in results:
            df = pd.read_csv(file, sep='|')
            dataframes.append(df)
        dataframes = pd.concat(dataframes, ignore_index=True)
        answers = list(dataframes['answer'])
        groundtruths = list(dataframes['groundtruth'])
        tropes = list(dataframes['trope'])

    category_result = {
        "Character Trait": {},
        "Role Interaction": {},
        "Situation": {},
        "Story Line": {},
        "Total": {}
    }
    for answer, groundtruth, trope in zip(answers, groundtruths, tropes):
        cat = trope_2_cat[trope]
        if trope not in category_result[cat]:
            category_result[cat][trope] = {
                'answers': [],
                'groundtruths': []
            }
        category_result[cat][trope]['answers'].append(1 if answer == 'yes' else 0)
        category_result[cat][trope]['groundtruths'].append(1 if groundtruth == 'yes' else 0)

        if trope not in category_result['Total']:
            category_result['Total'][trope] = {
                'answers': [],
                'groundtruths': []
            }
        category_result["Total"][trope]['answers'].append(1 if answer == 'yes' else 0)
        category_result["Total"][trope]['groundtruths'].append(1 if groundtruth == 'yes' else 0)

    for cat, result in category_result.items():
        gts = np.array([r['groundtruths'] for r in result.values()]).T
        preds = np.array([r['answers'] for r in result.values()]).T
        scores = precision_recall_fscore_support(gts, preds, average='micro')
        scores = {
            'precision': scores[0],
            'recall': scores[1],
            'f1': scores[2]
        }
        print('==============================================')
        print(cat)
        print(json.dumps(scores, indent=4))


if __name__ == '__main__':
    main()