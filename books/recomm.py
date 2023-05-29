import pickle
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from sklearn.metrics.pairwise import cosine_similarity

def my_view(request):
    # load the matrix from the pickle file
    with open('matrix.pkl', 'rb') as f:
        matrix = pickle.load(f)

    # subtract the mean from the rows
    matrix_norm = matrix.subtract(matrix.mean(axis=1), axis='rows')

    # calculate user similarity using cosine similarity
    user_similarity = cosine_similarity(matrix_norm.fillna(0))
    
    # remove picked user id from the candidate list
    picked_userid = request.GET.get('picked_userid')
    user_similarity = np.delete(user_similarity, picked_userid, axis=0)
    user_similarity = np.delete(user_similarity, picked_userid, axis=1)

    # number of similar users
    n = 10

    # User similarity threshold
    user_similarity_threshold = 0.1

    # Get top n similar users
    similar_users = np.argsort(user_similarity[:, picked_userid])[-n-1:-1][::-1]

    # Books that Targeted User has Read
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM matrix_norm WHERE id = '{picked_userid}'")
        picked_userid_watched = cursor.fetchone()
        cursor.execute(f"SELECT * FROM matrix_norm WHERE id IN ({','.join(map(str, similar_users))})")
        similar_users_books = cursor.fetchall()

    # A Dictionary to library item scores
    item_score = {}

    # loop through items
    for i in range(similar_users_books.shape[1]):
        # get the rating for book i
        book_rating = similar_users_books[:, i]

        # create a variable to store the score
        total = 0
        # create a variable to store the count
        count = 0

        # loop through similar users
        for u in similar_users:
            # if the book has rating
            if pd.isna(book_rating[u]) == False:
                # score is the sum of user similarity score multiply the book rating
                score = user_similarity[u, picked_userid] * book_rating[u]
                # Add the score to the total score for the book so far
                total += score
                # add 1 to the count
                count += 1

        # get the average score for the item
        if count > 0:
            item_score[i] = total / count

    # convert dictionary pandas dataframe
    item_score = pd.DataFrame(item_score.items(), columns=['book', 'book_score'])

    # sort the book by score
    ranked_item_score = item_score.sort_values(by='book_score', ascending=False)

    # select top m books
    m = 10

    # return the top m books as a JSON response
    return JsonResponse(ranked_item_score.head(m).to_dict())