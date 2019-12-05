class Annotation:
    
    @staticmethod
    def from_dump(dump_line):
        annotator_id, annotator, w1, w2, relation, gold_standard_relation, annotator_time_ms = list(map(str.strip, dump_line.split('|')))
        return Annotation(annotator + '_' + annotator_id, w1, w2, relation, gold_standard_relation if gold_standard_relation != '' else None, int(annotator_time_ms))
    
    @staticmethod
    def from_dump_with_timestamp(dump_line):
        annotator_id, annotator, _, w1, w2, relation, gold_standard_relation, annotator_time_ms, ts = list(map(str.strip, dump_line.split('|')))
        return Annotation(
            annotator + '_' + annotator_id,
            w1,
            w2,
            relation,
            gold_standard_relation if gold_standard_relation != '' else None, 
            int(annotator_time_ms),
            timestamp=ts
        )

    def __init__(self, annotator, w1, w2, relation, gold_standard_relation, annotator_time_ms, timestamp=None):
        self.annotator = annotator
        self.w1 = w1
        self.w2 = w2
        self.relation = relation
        self.gold_standard_relation = gold_standard_relation
        self.annotator_time_ms = annotator_time_ms
        self.timestamp = timestamp
        
    def is_valid(self):
        return self.annotator_time_ms >= 1000
    
    def is_gold_standard_exists(self):
        return self.gold_standard_relation is not None
    
    def is_gold_standard_agree(self):
        return self.relation == self.gold_standard_relation
        
    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return '{}({}, {}) | by: {} | time: {}'.format(self.relation, self.w1, self.w2, self.annotator, self.annotator_time_ms) \
                + (' | gold: {}'.format(self.gold_standard_relation) if self.gold_standard_relation is not None else '')
    
    
class AnnotatorProfile:
    
    def __init__(self, name, annotation_count, overall_agreement=0, hyponymy_agreement=0, unrelated_agreement=0):
        self.name = name
        self.annotation_count = annotation_count
        self.overall_agreement = overall_agreement
        self.hyponymy_agreement = hyponymy_agreement
        self.unrelated_agreement = unrelated_agreement

    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return '{} ({}) — Overall: {} | Hyponymy: {} | Unrelated: {}'.format(self.name, self.annotation_count, self.overall_agreement, self.hyponymy_agreement, self.unrelated_agreement)
    
