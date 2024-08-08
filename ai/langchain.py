import os
import json
import pinecone
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Pinecone
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from ai.ai_api import create_chat_message
from ai.tokens import count_message_tokens, count_string_tokens, get_tokens_limit
from ai.pplx import get_pplx_response

from dotenv import load_dotenv
load_dotenv()

RESPONSE_LENGTH = ['Concise', 'Normal', 'Detailed']
embeddings = OpenAIEmbeddings()
pinecone.init(api_key=os.environ["PINECONE_KEY"], environment=os.environ["PINECONE_ENVIRONMENT"])
index = pinecone.Index(os.environ["PINECONE_INDEX_NAME"])

def get_summarize_content(text: str):
    template = """{text}\n

    The above content is conversation histories.
    Please provide the summarized contents for next conversation from the above content.
    However, don't short too."""

    prompt = PromptTemplate(template=template, input_variables=["text"])

    llm = ChatOpenAI(model_name='gpt-4-1106-preview')
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    result = llm_chain.run(text)

    return result

def get_chat_history_str(message: str, summary: str, chat_history: list):
    result = ''
    pre_history = ''
    if summary != '':
        pre_history = 'Here are previous chat contents: \n' + summary + '\n'
    for item in chat_history:
        result += item['content'] + "\n"
    
    return pre_history + result + message

def get_chat_history_str_to_do(message: str, chat_history: list):
    result = ''

    reverse_chat_history = chat_history[::-1]
    for item in reverse_chat_history:
        result += item['content'] + "\n"
    
    return result + message

def get_questions_str(questions: list):
    result = ''

    for item in questions:
        result += item + '\n'
    
    return result

def get_ai_response_by_pinecone(message: str, chat_history: list, bot, summary: str = '', history_cursor: int = 0):
    
    vector_store = Pinecone(index, embeddings.embed_query, "text", bot["namespace"])
    
    length = len(chat_history)
    last_index = length
    query = get_chat_history_str(message = message, summary=summary, chat_history=chat_history[int(history_cursor):int(last_index)])
    tokens = count_string_tokens(query, 'gpt-3.5-turbo')
    
    limit = get_tokens_limit(model_name='gpt-4-1106-preview', max_token=800)

    new_history_cursor = history_cursor
    new_summary = summary
    if tokens > limit:
        
        if length > 8:
            chat_content = get_chat_history_str(message=message, summary=summary, chat_history=chat_history[int(history_cursor):int(length - 7)])
            new_history_cursor = length - 6
        else:
            chat_content = get_chat_history_str(message=message, summary=summary, chat_history=chat_history)
            new_history_cursor = length

        new_summary = get_summarize_content(chat_content)

        query = get_chat_history_str(message = message, summary=new_summary, chat_history=chat_history[int(new_history_cursor):int(last_index)])
    
    # pplx api
    pplx_response = get_pplx_response(bot['rolePrompt'], query)
    pplx_prompt =f"Here are data gotten from pplx. Please refer this data.\n------ start ------\n{pplx_response}\n------- end -------\n"   
    
    print('pplx_prompt', pplx_prompt)

    prompt_template = """{role_prompt} 

    {context}

    Question: {question}
    Helpful Answer:"""

    cite_prompt = ""
    if(bot["isCitingSource"]): cite_prompt = "You have to cite sources when answering."
    else: cite_prompt=""

    questions = ""
    if bot['botType'] == 2 and len(bot['questions']) > 0:
        questions = 'Here are the list of questions:\n' + get_questions_str(bot['questions'])

    initial_response_prompt = (
        f"{bot['rolePrompt']}\n"
        f"Your response must be {RESPONSE_LENGTH[int(bot['responseLength'])]}."
        f"{cite_prompt}"
        f"You have to speak in {bot['language']} throughout the conversation.\n"
        f"You will take into account the whole conversation, focusing on what is asked in the last user message."
        f"{pplx_prompt}"
        f"{questions}"
    )
    
    prompt_template = prompt_template.replace("{role_prompt}", initial_response_prompt)

    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    

    llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=bot['creativity'], max_tokens=800)
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )
    
    print('\n-------------------------- query ------------------------\n', query + '\n--------------------- end -------------------\n')
    
    result = qa_chain({"query": query})
    ai_response = result["result"]

    new_chat_history = chat_history
    new_chat_history.append(create_chat_message("user", message))
    new_chat_history.append(create_chat_message("assistant", ai_response))

    return {"ai_response": ai_response, "chat_history": new_chat_history, "summary": new_summary, "history_cursor": new_history_cursor}

def get_ai_response_qa(message: str, chat_history: list, bot, summary: str = '', history_cursor: int = 0):

    vector_store = Pinecone(index, embeddings.embed_query, "text", bot["namespace"])

    prompt_template = """{role_prompt} 

    {context}

    Question: {question}
    Helpful Answer:"""

    cite_prompt = ""
    if(bot["isCitingSource"]): cite_prompt = "You have to cite sources when answering."
    else: cite_prompt=""

    questions = ""
    if bot['botType'] == 2 and len(bot['questions']) > 0:
        questions = 'Here are the list of questions:\n' + get_questions_str(bot['questions'])

    initial_response_prompt = (
        f"{questions}\n"
        f"{bot['rolePrompt']}\n"
        f"Your response must be {RESPONSE_LENGTH[int(bot['responseLength'])]}."
        f"{cite_prompt}"
        f"You have to speak in {bot['language']} throughout the conversation.\n"
        f"You will take into account the whole conversation, focusing on what is asked in the last user message."
    )
    prompt_template = prompt_template.replace("{role_prompt}", initial_response_prompt)

    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=bot['creativity'], max_tokens=800)
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )
    
    length = len(chat_history)

    last_index = length
    print('last_index', last_index)
    print('history_cursor', history_cursor)
    query = get_chat_history_str(message = message, summary=summary, chat_history=chat_history[int(history_cursor):int(last_index)])
    tokens = count_string_tokens(query, 'gpt-3.5-turbo')
    
    print('--------------------------tokens:', tokens)
    limit = get_tokens_limit(model_name='gpt-4-1106-preview', max_token=800)
    print('----------------limit:', limit)

    new_history_cursor = history_cursor
    new_summary = summary
    if tokens > limit:
        
        if length > 8:
            chat_content = get_chat_history_str(message=message, summary=summary, chat_history=chat_history[int(history_cursor):int(length - 7)])
            new_history_cursor = length - 6
        else:
            chat_content = get_chat_history_str(message=message, summary=summary, chat_history=chat_history)
            new_history_cursor = length

        new_summary = get_summarize_content(chat_content)

        query = get_chat_history_str(message = message, summary=new_summary, chat_history=chat_history[int(new_history_cursor):int(last_index)])
        print('\n------------------ new_history_cursor:', new_history_cursor)
        print('\n------------------ summarized_content ---------------------\n', new_summary + '\n')

    print('\n-------------------------- query ------------------------\n', query + '\n--------------------- end -------------------\n')
    result = qa_chain({"query": query})

    ai_response = result["result"]

    print('---------------ai result-----------------\n', ai_response + "\n--------------end----------------\n")

    new_chat_history = chat_history
    new_chat_history.append(create_chat_message("user", message))
    new_chat_history.append(create_chat_message("assistant", ai_response))

    return {"ai_response": ai_response, "chat_history": new_chat_history, "summary": new_summary, "history_cursor": new_history_cursor}

def get_qna(message: str, chat_history: list, bot, summary: str = '', history_cursor: int = 0):

    vector_store = Pinecone(index, embeddings.embed_query, "text", bot["namespace"])

    prompt_template = """{role_prompt} 

    {context}

    Question: {question}
    Helpful Answer:"""

    questions = ""
    if bot['botType'] == 2 and len(bot['questions']) > 0:
        questions = 'The set of questions include:\n' + get_questions_str(bot['questions'])

    initial_response_prompt = (
        f"In this task, you will review a conversation and label the user’s responses to the questions from a specific list. You are required to pay close attention to the last question asked and whether its answer has been confirmed.\n"
        f"{questions}\n"
        f"The output format for the last question without a confirmed answer is:\n"
        f'@#("question":"question", "answer": "")@#\n'
        f'In this scenario, even if the user has provided an answer, it won’t be recorded in the “answer” field unless there is a subsequent confirmation question that the user has answered affirmatively.\n'
        f"The output format if the user’s answer to the last question does not match the question:\n"
        f'@#("question":"question", "answer": "")@#\n'
        f'Here, the user’s response doesn’t fit the question asked. The "answer" field remains empty, as the user’s response is not relevant or correct.\n'
        f"The output format when a user’s confirmed answer to the last question has been asked:\n"
        f'@#("question":"question", "answer": "answer")@#\n'
        f'This format is applied when a confirmation question has been asked and the user has confirmed their answer. The "answer" field will capture the user’s confirmed response.\n'
        f"If there is no question asked and no answer given, or if all conditions are not met, the output format is as follows:\n"
        f'@#("question":"", "answer": "")@#\n'
        f'Please ensure to match the question in the conversation with the closest question from the list provided above. However, if the user’s answer to the last question has not been confirmed, the “answer” field should remain empty.'
    )

    prompt_template = prompt_template.replace("{role_prompt}", initial_response_prompt)

    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=0, max_tokens=100)
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )
    
    length = len(chat_history)

    last_index = length

    query = get_chat_history_str(message = message, summary=summary, chat_history=chat_history[int(history_cursor):int(last_index)])
    tokens = count_string_tokens(query, 'gpt-3.5-turbo')
    
    limit = get_tokens_limit(model_name='gpt-4-1106-preview', max_token=800)

    new_history_cursor = history_cursor
    new_summary = summary
    if tokens > limit:
        
        if length > 8:
            chat_content = get_chat_history_str(message=message, summary=summary, chat_history=chat_history[int(history_cursor):int(length - 7)])
            new_history_cursor = length - 6
        else:
            chat_content = get_chat_history_str(message=message, summary=summary, chat_history=chat_history)
            new_history_cursor = length

        new_summary = get_summarize_content(chat_content)

        query = get_chat_history_str(message = message, summary=new_summary, chat_history=chat_history[int(new_history_cursor):int(last_index)])

    print('\n********************** query *************************\n', query + '\n******************** end ***********************\n')
    result = qa_chain({"query": query})

    ai_response = result["result"]
    json_data = {}
    
    if "@#" in ai_response:
        split_ai_response = ai_response.split('@#')
        replace_data = split_ai_response[1]
        replace_data = replace_data.replace('(', '{')
        replace_data = replace_data.replace(')', '}')

        print('replace_data', replace_data)

        json_data = json.loads(replace_data)

    result = None
    if json_data['answer'] != '':
        result = json_data

    print('******************ai result****************\n', result)

    return result

def get_ai_response_by_pinecone_to_do(message: str, chat_history: list, bot, to_do: list = []):

    vector_store = Pinecone(index, embeddings.embed_query, "text", bot["namespace"])

    prompt_template = """{role_prompt} 

    {context}

    Question: {question}
    Helpful Answer:"""

    current_to_do_data = ''

    if len(to_do) != 0:
        current_to_do_data += json.dumps(to_do)
        current_to_do_data = current_to_do_data.replace('{', '(')
        current_to_do_data = current_to_do_data.replace('}', ')')
        current_to_do_data = 'Here are user current to-do list.\n' + '@' + current_to_do_data + '@'

    initial_response_prompt = (
        f"{bot['rolePrompt']}\n"
        f'{current_to_do_data}'
    )

    print('initial prompt\n********************start**********************\n', initial_response_prompt+'\n*******************end***************************\n')
    prompt_template = prompt_template.replace("{role_prompt}", initial_response_prompt)

    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=bot['creativity'], max_tokens=800)
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )

    query = get_chat_history_str_to_do(message, chat_history[-1:-8:-1])
    print('query\n**************************start***************************\n', query + '\n*************************end***************************')
    
    result = qa_chain({"query": query})

    ai_response = result["result"]

    new_chat_history = chat_history
    new_chat_history.append(create_chat_message("user", message))
    new_chat_history.append(create_chat_message("assistant", ai_response))

    return {"ai_response": ai_response, "chat_history": new_chat_history}

def get_to_do(message: str, chat_history: list, bot,  to_do: list = []):

    vector_store = Pinecone(index, embeddings.embed_query, "text", bot["namespace"])

    prompt_template = """{role_prompt} 

    {context}

    Question: {question}
    Helpful Answer:"""

    current_to_do_data = ''

    if len(to_do) != 0:
        current_to_do_data += json.dumps(to_do)
        current_to_do_data = current_to_do_data.replace('{', '(')
        current_to_do_data = current_to_do_data.replace('}', ')')
        current_to_do_data = 'Here are user current to-do list.\n' + '@' + current_to_do_data + '@'

    initial_response_prompt = (
        f"Here is a first role:\n"
        f"{bot['rolePrompt']}\n"
        f'Here is the second role:\n'
        f'As an AI assistant, your main role is to help the user manage their tasks effectively. This involves tracking tasks, categorizing them, assigning priority, and updating their status as completed when needed. Here are the detailed guidelines to follow:\n'
        f'1. When a user mentions a task, classify it into relevant categories such as work, personal, health, or social. If there are specific steps associated with the task, note them down in the ‘instructions’ field. Assign a numerical ‘priority’ value based on the sequence in which tasks are mentioned, starting with ‘1’ and increasing by ‘1’ for each subsequent task. If no tasks are mentioned, leave the ‘title’ and ‘instructions’ fields empty, ‘priority’ as ‘0’, and ‘completed’ as ‘false’.\n'
        f'2. Maintain a continuous list of tasks. If the user says ‘Add a task’, followed by the task details, append this new task to the existing list, assigning it the next available ‘priority’ number. The list should grow as new tasks are added and it should not overwrite the existing tasks.\n'
        f'3. If a user says ‘Complete a task’, followed by one or more task names, find those specific tasks in the list and change their ‘completed’ status to ‘true’. Then reset their ‘priority’ to ‘0’. For the remaining tasks, reassign the ‘priority’ numbers, ensuring they decrease by the number of tasks completed and the list is always sorted by ‘priority’. In case of a tie (multiple tasks with ‘priority’ ‘0’), the tasks should retain their original order.\n'
        f'4. Present the tasks in a format like this: ‘@[("title": "<task>", "category": "<category>", "instructions": "<instructions>", "priority": "<priority>", "completed": "<true/false>")]@’. The tasks should maintain their sequence as they were added and updated.\n'
        f'5. If the user says ‘Complete a task’ but doesn’t specify which one, prompt them to provide the task name. For example, ‘Sure, which task have you completed?’ Then update the ‘completed’ status and ‘priority’ of the specified task(s) accordingly.\n'
        f'Your primary goal is to keep the user organized and aid them in managing their tasks efficiently. In case multiple tasks are completed simultaneously, adjust the ‘priority’ of the remaining tasks appropriately to maintain order and coherence in the task list.\n'
        f'Never change user current to-do list except to add or complete tasks.\n'
        f'{current_to_do_data}\n'
        f'output format:\n'
        f'<content>@[("title": "<task>", "category": "<category>", "instructions": "<instructions>", "priority": "<priority>", "completed": "<true/false>")]@\n'
        f'<content> should be AI response for first role.'
    )

    print('initial prompt\n-------------------------start--------------------------\n', initial_response_prompt+'\n--------------------end---------------------\n')
    prompt_template = prompt_template.replace("{role_prompt}", initial_response_prompt)

    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=0, max_tokens=1600)
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )

    query = get_chat_history_str_to_do(message, chat_history[-1:-6:-1])
    print('query\n---------------------start---------------------\n', query + '\n----------------end-------------')
    result = qa_chain({"query": query})
    ai_response = result["result"]

    print('ai_response\n-----------start--------------------\n', ai_response + '\n----------------end--------------------')
    to_do_data = to_do

    split_ai_response = ai_response.split('@')

    print('split_ai_response\n---------------start--------------\n', split_ai_response)
    
    if "@" in ai_response:
        replace_data = split_ai_response[1]
        replace_data = replace_data.replace('(', '{')
        replace_data = replace_data.replace(')', '}')
        json_data = json.loads(replace_data)
        to_do_data = json_data
    
    print('to_do_data\n---------------start--------------\n', to_do_data)

    new_chat_history = chat_history
    new_chat_history.append(create_chat_message("user", message))
    new_chat_history.append(create_chat_message("assistant", split_ai_response[0]))

    return {"ai_response": split_ai_response[0], "to_do_data": to_do_data, "chat_history": new_chat_history}

def compare_message_chat_history(message: str, chat_history:list):
    flag = False
    
    if len(chat_history) > 2:
        last_chat_history = chat_history[-2]['content']
    
        if message == last_chat_history:
            flag = True

    return flag