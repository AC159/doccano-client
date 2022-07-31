from allennlp.predictors.predictor import Predictor

# ner_fine_grained = Predictor.from_path(
#     "https://storage.googleapis.com/allennlp-public-models/fine-grained-ner.2021-02-11.tar.gz")
# ner_elmo = Predictor.from_path(
#     "https://storage.googleapis.com/allennlp-public-models/ner-elmo.2021-02-12.tar.gz")


# This function gives priority to the fine grained model, In case the word doesn't have a tag, we take the elmo tag
# for this word
def merge_results(fine_grained, elmo):
    result = []
    for i in range(len(fine_grained)):
        if fine_grained[i] == 'O':
            result.append(elmo[i])
        else:
            result.append(fine_grained[i])
    return result


# This function merges the words whose tags are between B-I-L, It will need a small change to remove the prefix and
# and return the tag instead of the words
def extract_person_and_place(fine_grained, elmo):
    output = []
    for i in range(len(fine_grained['tags'])):
        word = []
        if fine_grained['tags'][i].startswith('U-') or elmo['tags'][i].startswith('U-'):
            output.append(fine_grained['words'][i])
        elif fine_grained['tags'][i].startswith('B-') or elmo['tags'][i].startswith('B-'):
            word.append(fine_grained['words'][i])
        elif fine_grained['tags'][i].startswith('I-') or elmo['tags'][i].startswith('I-'):
            word.append(fine_grained['words'][i])
        elif fine_grained['tags'][i].startswith('L-') or elmo['tags'][i].startswith('L-'):
            word.append(fine_grained['words'][i])
            output.append(' '.join(word))
            word = []
    return output


# def predict(sentence):
#     fine_grained_output = ner_fine_grained.predict(sentence=sentence)
#     elmo_output = ner_elmo.predict(sentence=sentence)
#     result = merge_results(fine_grained_output['tags'], elmo_output['tags'])
#     output = extract_person_and_place(fine_grained_output, elmo_output)
#     return output
