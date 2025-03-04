from collections import defaultdict

places = {
    "Central Park": ["park", "nature", "walking", "picnic"],
    "Eiffel Tower": ["landmark", "history", "view", "photography"],
    "Golden Gate Bridge": ["bridge", "landmark", "view", "photography"],
    "Yosemite National Park": ["park", "nature", "hiking", "camping"],
    "Louvre Museum": ["museum", "art", "history", "indoor"]
}


inverted_index = defaultdict(list)
for place, tags in places.items():
    for tag in tags:
        inverted_index[tag].append(place)

print("Инвертированный индекс:")
print({tag: places for tag, places in inverted_index.items()})
#####################################################


def shunting_yard(query):
    precedence = {'not': 3, 'and': 2, 'or': 1}
    output = []
    operator_stack = []
    tokens = query.lower().split()
    
    for token in tokens:
        if token in ['and', 'or', 'not']:
            while (operator_stack and 
                   operator_stack[-1] != '(' and 
                   precedence[token] <= precedence.get(operator_stack[-1], 0)):
                output.append(operator_stack.pop())
            operator_stack.append(token)
        elif token == '(':
            operator_stack.append(token)
        elif token == ')':
            while operator_stack[-1] != '(':
                output.append(operator_stack.pop())
            operator_stack.pop()
        else:
            output.append(token)
    
    while operator_stack:
        output.append(operator_stack.pop())
    
    return output

def boolean_search(query, inverted_index, all_docs):
 
    postfix_query = shunting_yard(query)
    stack = []
    
    for token in postfix_query:
        if token == 'and':
            if len(stack) < 2:
                raise ValueError("Недостаточно операндов для AND")
            b = set(stack.pop())
            a = set(stack.pop())
            stack.append(a & b)
        elif token == 'or':
            if len(stack) < 2:
                raise ValueError("Недостаточно операндов для OR")
            b = set(stack.pop())
            a = set(stack.pop())
            stack.append(a | b)
        elif token == 'not':
            if len(stack) < 1:
                raise ValueError("Недостаточно операндов для NOT")
            a = set(stack.pop())
            stack.append(set(all_docs) - a)
        else:
            stack.append(set(inverted_index.get(token, [])))
    
    if len(stack) != 1:
        raise ValueError("Некорректный запрос")
    
    return list(stack[0])

# # Пример использования
# places = {
#     "Central Park": ["park", "nature", "walking", "picnic"],
#     "Eiffel Tower": ["landmark", "history", "view", "photography"],
#     "Golden Gate Bridge": ["bridge", "landmark", "view", "photography"],
#     "Yosemite National Park": ["park", "nature", "hiking", "camping"],
#     "Louvre Museum": ["museum", "art", "history", "indoor"]
# }

inverted_index = defaultdict(list)
for place, tags in places.items():
    for tag in tags:
        inverted_index[tag].append(place)

all_docs = list(places.keys())

queries = [
    "park AND nature",
    "landmark OR view",
    "history AND NOT museum",
    "(park OR landmark) AND NOT art"
]

print("Результаты поиска:")
for query in queries:
    try:
        result = boolean_search(query, inverted_index, all_docs)
        print(f"Запрос: '{query}'\nРезультат: {sorted(result)}\n")
    except ValueError as e:
        print(f"Ошибка: {e}\n")

#################################################################

import math

def calculate_tfidf(places):
    tf = {place: defaultdict(int) for place in places}
    
    df = defaultdict(int)
    
    for place, tags in places.items():
        for tag in set(tags):
            df[tag] += 1
        for tag in tags:
            tf[place][tag] += 1
    
    for place in tf:
        total_tags = len(places[place])
        for tag in tf[place]:
            tf[place][tag] /= total_tags
    
    
    total_places = len(places)
    idf = {tag: math.log(total_places / df[tag]) for tag in df}
    
    
    tfidf = {place: {tag: tf_val * idf[tag] for tag, tf_val in tags.items()} 
             for place, tags in tf.items()}
    
    return tfidf

def rank_results(query_tags, tfidf):
    scores = {}
    for place, tags in tfidf.items():
        score = sum(tags.get(tag, 0) for tag in query_tags)
        scores[place] = score
    return sorted(scores.items(), key=lambda x: -x[1])

tfidf = calculate_tfidf(places)
query_tags = ["park", "nature"]
ranked = rank_results(query_tags, tfidf)

print("\nРанжирование по TF-IDF для тегов ['park', 'nature']:")
for place, score in ranked:
    print(f"{place}: {score:.2f}")