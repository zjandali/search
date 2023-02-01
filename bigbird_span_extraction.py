from transformers import BigBirdTokenizer
from transformers import BigBirdForQuestionAnswering
import torch

model = BigBirdForQuestionAnswering.\
    from_pretrained('google/bigbird-base-trivia-itc') # maybe not this one that has
# the classifier weights
tokenizer = BigBirdTokenizer.\
    from_pretrained('google/bigbird-base-trivia-itc') #has to be squad?
torch.set_grad_enabled(False)
def answer_question(question, answer_text):
    '''
    Takes a `question` string and an `answer_text` string (which contains the
    answer), and identifies the words within the `answer_text` that are the
    answer. Prints them out.
    '''
    # ======== Tokenize ========
    # Apply the tokenizer to the input text, treating them as a text-pair.
    input_ids = tokenizer.encode(question, answer_text)

    # Report how long the input sequence is.
    # print('Query has {:,} tokens.\n'.format(len(input_ids)))

    # ======== Set Segment IDs ========
    # Search the input_ids for the first instance of the `[SEP]` token.
    sep_index = input_ids.index(tokenizer.sep_token_id)

    # The number of segment A tokens includes the [SEP] token istelf.
    num_seg_a = sep_index + 1

    # The remainder are segment B.
    num_seg_b = len(input_ids) - num_seg_a

    # Construct the list of 0s and 1s.
    segment_ids = [0]*num_seg_a + [1]*num_seg_b

    # There should be a segment_id for every input token.
    assert len(segment_ids) == len(input_ids)


    # ======== Evaluate ========
    # Run our example question through the model.
    model_result = model(torch.tensor([input_ids]),
                         # The tokens representing our input text.
                                    token_type_ids=torch.tensor([segment_ids]))
    # The segment IDs to differentiate question from answer_text

    start_scores = model_result.start_logits
    end_scores = model_result.end_logits
    # ======== Reconstruct Answer ========
    # Find the tokens with the highest `start` and `end` scores.
    answer_start = torch.argmax(start_scores)
    answer_end = torch.argmax(end_scores)

    # Get the string versions of the input tokens.
    tokens = tokenizer.convert_ids_to_tokens(input_ids)

    # Start with the first token.
    answer = tokens[answer_start]

    # Select the remaining answer tokens and join them with whitespace.
    for i in range(answer_start + 1, answer_end + 1):

        # If it's a subword token, then recombine it with the previous token.
        if tokens[i][0:2] == '##':
            answer += tokens[i][2:]

        # Otherwise, add a space then the token.
        else:
            answer += ' ' + tokens[i]

    start_score = torch.max(start_scores)
    end_score = torch.max(end_scores)
    return (start_score + end_score)/2, answer, answer_start, answer_end

def answer_question_from_parts(question, answer_texts):
    '''
    Takes a `question` string and `answer_texts` list of strings (at least one of which contains the
    answer), concatenates the strings in `answer_texts` together, and finds the answer
    within this long string. Then returns the answer and the indices of `answer_texts`
    that contain this answer.
    '''
    # ======== Tokenize ========
    # Apply the tokenizer to the input text, treating them as a text-pair.
    tokenized_query = tokenizer.tokenize(question)
    tokenized_text = []
    indices = []
    for i in answer_texts:
        t = tokenizer.tokenize(i)
        tokenized_text.extend(t)
        indices.append(len(tokenized_text) + len(tokenized_query))
    input_ids = tokenizer.encode(tokenized_query, tokenized_text)

    # Report how long the input sequence is.
    # print('Query has {:,} tokens.\n'.format(len(input_ids)))

    # ======== Set Segment IDs ========
    # Search the input_ids for the first instance of the `[SEP]` token.
    sep_index = input_ids.index(tokenizer.sep_token_id)

    # The number of segment A tokens includes the [SEP] token istelf.
    num_seg_a = sep_index + 1

    # The remainder are segment B.
    num_seg_b = len(input_ids) - num_seg_a

    # Construct the list of 0s and 1s.
    segment_ids = [0]*num_seg_a + [1]*num_seg_b

    # There should be a segment_id for every input token.
    assert len(segment_ids) == len(input_ids)


    # ======== Evaluate ========
    # Run our example question through the model.
    model_result = model(torch.tensor([input_ids]),
                         # The tokens representing our input text.
                                    token_type_ids=torch.
                         tensor([segment_ids]))
    # The segment IDs to differentiate question from answer_text

    start_scores = model_result.start_logits
    end_scores = model_result.end_logits
    # ======== Reconstruct Answer ========
    # Find the tokens with the highest `start` and `end` scores.
    answer_start = torch.argmax(start_scores)
    answer_end = torch.argmax(end_scores)

    # Get the string versions of the input tokens.
    tokens = tokenizer.convert_ids_to_tokens(input_ids)

    # Start with the first token.
    answer = tokens[answer_start]

    # Select the remaining answer tokens and join them with whitespace.
    for i in range(answer_start + 1, answer_end + 1):

        # If it's a subword token, then recombine it with the previous token.
        if tokens[i][0:2] == '##':
            answer += tokens[i][2:]

        # Otherwise, add a space then the token.
        else:
            answer += ' ' + tokens[i]

    answer_in = []
    started = False
    for i in range(len(indices)):
        if answer_start < indices[i]:
            started = True
        if started:
            answer_in.append(i)
            if answer_end < indices[i]:
                break

    return answer, answer_in

# Find answer in a whole page of text.
text = '''
P Q P∧Q
T T T
T F F
F T F
F F F
P ¬P
T F
F T
Sanity check! What is the truth table for disjunction (OR)?
So far, we introduced the connectives AND, OR, and NOT. Now that we’re warmed up, let us introduce a
fourth connective, which is a bit trickier but possibly the most important:
4. Implication (IMPLIES, =⇒): P =⇒ Q (i.e. “P implies Q"). This is the same as “If P, then Q."
Intuitively, the way you should think about implication is that it is only false when P is true and Q is false.
Formally, here is the truth table:
P Q P =⇒ Q
T T T
T F F
F T T
F F T
A useful fact to keep in mind is that P =⇒ Q is equivalent to the statement ¬P∨Q.
Sanity check! Write down the truth table for ¬P∨Q. Does it match that for P =⇒ Q, as claimed?
2.1 The contrapositive and converse
Thus far, we have introduced the concept of a proposition, along with connectives AND, OR, NOT, and
IMPLIES. We now explore two fundamental statements which are closely related to P =⇒ Q. They are the
contrapositive and the converse:
1. Contrapositive: ¬Q =⇒ ¬P.
2. Converse: Q =⇒ P.
One of these is logically equivalent to P =⇒ Q, and the other is not. Can you tell which is which? How
would you formally check your guess? One way is to write down the truth tables and compare them:
P Q ¬P ¬Q P =⇒ Q Q =⇒ P ¬Q =⇒ ¬P
T T F F T T T
T F F T F T F
F T T F T F T
F F T T T T T
'''
page_answer = answer_question('what is the contrapositive?', text)
print(page_answer)
