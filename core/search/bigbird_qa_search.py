from transformers import BigBirdTokenizer
from transformers import BigBirdForQuestionAnswering
from core.weaviate.operations import search_qa
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
Academic writing has undergone significant transformations over the centuries, adapting to the changing landscapes of education, technology, and society. Initially, scholarly works were accessible only to a privileged few, often confined within the walls of elite institutions. The advent of the printing press in the 15th century democratized knowledge dissemination, allowing scholarly works to reach a broader audience.

In the contemporary era, the digital revolution has further expanded the reach of academic writing. Online platforms and open-access journals have made research findings readily available to anyone with internet access. This shift has not only increased the accessibility of scholarly works but has also introduced new challenges, such as ensuring the credibility and quality of information.

The structure of academic texts has also evolved to meet the needs of diverse disciplines. Traditional essays typically follow a three-part structure: introduction, body, and conclusion. This format provides a clear and logical flow, enabling readers to follow the argument and navigate the text effectively. In contrast, scientific papers often adhere to the IMRaD structure—Introduction, Methods, Results, and Discussion—which facilitates the presentation of empirical research in a systematic manner. 
LINNAEUS UNIVERSITY

Language use in academic writing has become more standardized, emphasizing formality, objectivity, and precision. Writers are encouraged to avoid colloquialisms and personal pronouns, striving instead for a tone that conveys impartiality and professionalism. This standardization helps maintain the integrity of academic discourse across various fields of study. 
QUIZLET

Moreover, the integration of diverse perspectives has enriched academic writing. Interdisciplinary approaches have led to more comprehensive analyses, fostering a deeper understanding of complex issues. Collaborative research and writing have become more prevalent, reflecting the interconnected nature of modern scholarship.

In conclusion, academic writing continues to evolve, influenced by technological advancements, changing educational paradigms, and the increasing emphasis on accessibility and inclusivity. As it adapts to these developments, the core principles of clarity, rigor, and scholarly integrity remain steadfast, ensuring that academic writing retains its vital role in the pursuit of knowledge.
'''
page_answer = answer_question('What invention in the 15th century significantly increased the accessibility of scholarly works?', text)
print(page_answer)

def weaviate_bigbird_qa(client, question, limit=5):
    """
    Performs two-stage question answering:
    1. Uses Weaviate to retrieve relevant passages
    2. Uses BigBird to extract the exact answer from those passages
    """
    # Initialize BigBird model and tokenizer
    model = BigBirdForQuestionAnswering.from_pretrained('google/bigbird-base-trivia-itc')
    tokenizer = BigBirdTokenizer.from_pretrained('google/bigbird-base-trivia-itc')
    torch.set_grad_enabled(False)
    
    # Get relevant passages from Weaviate
    weaviate_results = search_qa(client, question, limit=limit)
    answers = []
    
    # Process each passage with BigBird
    for result in weaviate_results:
        context = result['content']
        
        # ======== Tokenize ========
        input_ids = tokenizer.encode(question, context)
        
        # ======== Set Segment IDs ========
        sep_index = input_ids.index(tokenizer.sep_token_id)
        num_seg_a = sep_index + 1
        num_seg_b = len(input_ids) - num_seg_a
        segment_ids = [0]*num_seg_a + [1]*num_seg_b
        assert len(segment_ids) == len(input_ids)

        # ======== Evaluate ========
        model_result = model(torch.tensor([input_ids]), 
                           token_type_ids=torch.tensor([segment_ids]))
        
        start_scores = model_result.start_logits
        end_scores = model_result.end_logits
        
        # ======== Reconstruct Answer ========
        answer_start = torch.argmax(start_scores)
        answer_end = torch.argmax(end_scores)
        tokens = tokenizer.convert_ids_to_tokens(input_ids)
        
        answer = tokens[answer_start]
        for i in range(answer_start + 1, answer_end + 1):
            if tokens[i][0:2] == '##':
                answer += tokens[i][2:]
            else:
                answer += ' ' + tokens[i]

        start_score = torch.max(start_scores)
        end_score = torch.max(end_scores)
        confidence = float((start_score + end_score)/2)
        
        answers.append({
            'answer': answer,
            'confidence': confidence,
            'context': context,
            'document': result['document'],
            'page': result['page'],
            'paragraph': result['paragraph']
        })
    
    # Sort answers by confidence score
    answers.sort(key=lambda x: x['confidence'], reverse=True)
    
    return answers
