
import json
import random

def shuffle_prisms_and_ids(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    for case in data.get('cases', []):
        prisms = case.get('input', {}).get('prisms', [])
        if not prisms:
            continue

        # Shuffle the order of prisms
        random.shuffle(prisms)

        # Shuffle the ids
        original_ids = [p['id'] for p in prisms]
        shuffled_ids = original_ids[:]
        random.shuffle(shuffled_ids)
        id_map = {old_id: new_id for old_id, new_id in zip(original_ids, shuffled_ids)}

        # Update prism ids
        for prism in prisms:
            prism['id'] = id_map[prism['id']]

        # Update sequence ids
        sequence = case.get('expected', {}).get('sequence', [])
        if sequence:
            new_sequence = [id_map.get(seq_id, seq_id) for seq_id in sequence]
            case['expected']['sequence'] = new_sequence

    return data

if __name__ == '__main__':
    shuffled_data = shuffle_prisms_and_ids('canonical-data.json')
    with open('shuffled-canonical-data.json', 'w') as f:
        f.write('{\n')
        f.write('  "exercise": "prism",\n')
        f.write('  "cases": [\n')
        for i, case in enumerate(shuffled_data['cases']):
            f.write('    {\n')
            for key, value in case.items():
                if key == 'input':
                    f.write('      "input": {\n')
                    for input_key, input_value in value.items():
                        if input_key == 'prisms':
                            f.write('        "prisms": [\n')
                            for j, prism in enumerate(input_value):
                                f.write('          ' + json.dumps(prism))
                                if j < len(input_value) - 1:
                                    f.write(',\n')
                                else:
                                    f.write('\n')
                            f.write('        ]\n')
                        else:
                            f.write(f'        "{input_key}": {json.dumps(input_value)},\n')
                    f.write('      },\n')
                elif key == 'expected':
                    f.write('      "expected": {\n')
                    for expected_key, expected_value in value.items():
                        f.write(f'        "{expected_key}": {json.dumps(expected_value)}\n')
                    f.write('      }\n')
                else:
                    f.write(f'      "{key}": {json.dumps(value)},\n')
            f.write('    }')
            if i < len(shuffled_data['cases']) - 1:
                f.write(',\n')
            else:
                f.write('\n')
        f.write('  ]\n')
        f.write('}\n')
