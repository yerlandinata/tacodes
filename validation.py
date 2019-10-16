from .hypernymy import HypernymyRelation

class Validator:

    TRUE_POSITIVE = 'true_positive'
    TRUE_NEGATIVE = 'true_negative'
    FALSE_POSITIVE = 'false_positive'
    FALSE_NEGATIVE = 'false_negative'
        
    def __init__(self, file_name='validation/validation.csv'):
        with open(file_name, 'r') as f:
            lines = f.readlines()
        lines = list(map(str.strip, lines))
        self.__gold_true = set()
        self.__gold_false = set()
        for line in lines:
            hypernym, hyponym, label = line.split(', ')
            if label == '1':
                self.__gold_true.add(HypernymyRelation(hypernym, hyponym))
            else:
                self.__gold_false.add(HypernymyRelation(hypernym, hyponym))

    def validate(self, all_pairs_set):
        report = ''
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        for p in self.__gold_true:
            if p in all_pairs_set:
                tp += 1
                report += str(p) + ' : ' + Validator.TRUE_POSITIVE + '\n'
            else:
                fn += 1
                report += str(p) + ' : ' + Validator.FALSE_NEGATIVE + '\n'
        for p in self.__gold_false:
            if p in all_pairs_set:
                fp += 1
                report += str(p) + ' : ' + Validator.FALSE_POSITIVE + '\n'
            else:
                tn += 1
                report += str(p) + ' : ' + Validator.TRUE_NEGATIVE  + '\n'
        precision = tp/(tp+fp)
        recall = tp/(tp+fn)
        accuracy = (tp+tn)/(tp+tn+fp+fn)
        f1 = 2*precision*recall/(precision+recall)
        report = 'TP: {} | TN: {} | FP: {} | FN: {} |\n PRECISION: {} | RECALL: {} | ACCURACY: {} | F1: {} |\n'.format(
            tp, tn, fp, fn, precision, recall, (tp+tn)/(tp+tn+fp+fn), f1
        ) + report
        return report

