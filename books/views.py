from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Pdf_Info, Review
from .form import *
from .recomm import *
import pickle
import numpy as np
# from django.http import JsonResponse
# from django.db.models import Avg
# from django.views.decorators.http import require_http_methods
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth import authenticate
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# Create your views here.

def digital_books(request, pram = None):
    book = Pdf_Info.objects.all()
    if pram is not None:
        book=book.filter(title__startswith=pram)
    context = {
        'book':book
    }

    return render(request, 'books/home.html', context)

def view_book(request):
    book = Pdf_Info.objects.all()
    context={
        'book':book
    }
    return render(request, 'books/view_books.html', context)


@staff_member_required()
def add_Book(request,pk=None):
    form = BookForm()#improt productform form form.py
    if request.method == 'POST':
        form = BookForm(request.POST,request.FILES)#request.File send request to the file to be uploaded to uploade the file, without it there would be error while saving file
        print(form)
        if form.is_valid():
            review = form.save(commit=False)
            review.save()
            messages.success(request, 'product added succcssfully')
            return redirect('books:digital_books')
        else:
            messages.error(request, 'Failed to add Product')
    
    context = {
        'form':form
    }
    return render(request, 'books/addbook.html', context)


def book_detail(request, slug):
    # book = get_object_or_404(Pdf_Info, slug = slug)
    # book = Pdf_Info.objects.get(slug=slug)
    book = Pdf_Info.objects.filter(slug = slug).first()
    # books.user_rating = rating.rating if rating else 0
    
    if request.method == "POST":
        rating = request.POST.get('rating')
        content = request.POST.get("content",'')
        
        if content:
            reviews = Review.objects.filter(created_by=request.user, book = book)
            
            if reviews.count() > 0:
                review = reviews.first()
                review.rating = rating
                review.content = content
                review.save()
            
            else:
                review = Review.objects.create(
                    book = book,
                    rating = rating,
                    content = content,
                    created_by= request.user
                )
            
            return redirect('books:book_detail', slug = slug)
        
    context = {'book':book}
    
    return render(request, 'books/book_detail.html', context)


@staff_member_required()
def delete_book(request, pk):
    book = Pdf_Info.objects.filter(id = pk)
    
    # if request. != item.created_by:
    #     messages.INFO(request, 'You are not authorized')
    
    if request.method == 'POST':
        book.delete()
        return redirect('books:digital_books')

    context = {
        'book':book
    }
    return render(request, 'books/delete.html', context)



def search(request):
    queries = request.GET.get('query', False)# here 'query' is from 'name= query' in navbar
    if len(queries) > 50:
        book = Pdf_Info.objects.none()
    else:
        book = Pdf_Info.objects.filter(title__icontains = queries)

    if book.count() == 0:
        messages.warning(request, 'Search result not found.Please search again.')
    context = {
        'book':book,
        'queries':queries ,
        # 'recommended_books' : recommended_books
    }
    return render(request, 'books/search.html', context)



# @app.route()
def recommend(request):
    # books = Pdf_Info.objects.all()
    popular_df = pickle.load(open('popular.pkl', 'rb'))
    pt = pickle.load(open('pt.pkl', 'rb'))
    # books = pickle.load(open('books.pkl', 'rb'))
    books = pd.DataFrame(list(Pdf_Info.objects.all().values()))
    similarity_scores= pickle.load(open('similarity_scores.pkl', 'rb'))
    # index = None
    if request.method == 'POST':
        # index fetch
        user_input = request.POST.get('user_input')
        # index = np.where(pt.index == user_input)[0][0]
        index_array = np.where(pt.index == user_input)[0]
        if len(index_array) > 0:
            index = index_array[0]
            # Rest of the code
        
            similar_items = sorted(list(enumerate(similarity_scores[index])),key=lambda x:x[1],reverse=True)[1:9]
        
            data = []
            for i in similar_items:
                item = []
                temp_df = books[books['title'] == pt.index[i[0]]]
                item.extend(list(temp_df.drop_duplicates('title')['title'].values))
                item.extend(list(temp_df.drop_duplicates('title')['author'].values))
                item.extend(list(temp_df.drop_duplicates('title')['image'].values))
                # item.extend(list(temp_df.drop_duplicates('title')['image'].apply(lambda x: f"/media/{x}").values))

                
                data.append(item)
            
            print(data)
            
            context = {
                'data' : data
            }
            return render(request, 'books/recommendation.html', context)
        else:
            messages.info(request, 'recommendation not found')
            
    return render(request, 'books/recommendation.html')


@login_required
def get_recommendations(request):
    # Load the matrix from the pickle file
    matrix = pd.read_pickle('matrix.pkl')
    
    # Get the currently logged-in user id
    picked_userid = request.user.id
    
    if picked_userid not in matrix.index:
        return HttpResponse('No Recommendations available', status = 200)
    
    # Subtract the mean from each row of the matrix
    matrix_norm = matrix.subtract(matrix.mean(axis=1), axis='rows')

    # Calculate user similarity
    user_similarity = matrix_norm.T.corr()
    user_similarity_cosine = cosine_similarity(matrix_norm.fillna(0))

    # Remove the picked user id from the candidate list
    user_similarity.drop(index=picked_userid, inplace=True)

    # Number of similar users
    n = 10

    # User similarity threshold
    user_similarity_threshold = 0.1

    # Get top n similar users
    similar_users = user_similarity[user_similarity[picked_userid] > user_similarity_threshold][picked_userid]

    # Books that Targeted User has Read
    picked_userid_watched = matrix_norm[matrix_norm.index == picked_userid].dropna(axis=1, how='all')
    similar_users_books = matrix_norm[matrix_norm.index.isin(similar_users.index)].dropna(axis=1, how='all')

    item_score = {}

    # Loop through items
    for i in similar_users_books.columns:
        # Get the rating for book i
        book_rating = similar_users_books[i]
        # Create variables to store the score and count
        total = 0
        count = 0
        # Loop through similar users
        for u in similar_users.index:
            # If the user has rated the book
            if pd.isna(book_rating[u]) == False:
            
                # Calculate the score
                score = similar_users[u] * book_rating[u]
                # Add the score to the total
                total += score
                # Increment the count
                count += 1
        # Calculate the average score for the book
        item_score[i] = {
            'title': i[0],
            'description': i[1],
            'isbn': i[2],
            'author': i[3],
            'image' : i[4],
            'book_pdf' : i[5],
            'book_score': total / count if count > 0 else 0,
        }
        
    # Convert the dictionary to a dataframe
    item_score_df = pd.DataFrame.from_dict(item_score, orient='index')

    # Sort the books by score
    ranked_item_score = item_score_df.sort_values(by='book_score', ascending=False)

    # Select the top m books
    m = 10
    top_books = ranked_item_score.head(m)
    print(top_books) 
    # Render the recommendations template with the top_books as context
    return render(request, 'books/result.html', {'top_books': top_books})


@login_required
def recommendations(request):
    # Load the matrix from the pickle file
    matrix = pd.read_pickle('matrix.pkl')
    
    # Get the currently logged-in user id
    picked_userid = request.user.id
    if picked_userid not in matrix.index:
        return HttpResponse('No Recommendation abailable.', status = 200)
    
    # Subtract the mean from each row of the matrix
    matrix_norm = matrix.subtract(matrix.mean(axis=1), axis='rows')

    # Calculate user similarity
    # user_similarity = matrix_norm.T.corr()
    user_similarity_cosine = cosine_similarity(matrix_norm.fillna(0))

    user_similarity_cosine_df = pd.DataFrame(user_similarity_cosine)
    # remove picked user id from the candidate list

    if picked_userid in user_similarity_cosine_df.index:
        user_similarity_cosine_df.drop(index=picked_userid, inplace=True)
    else:
        return HttpResponse('No Recommendation abailable.', status = 200)

    # Number of similar users
    n = 10

    # User similarity threshold
    user_similarity_threshold = 0.1

    # Get top n similar users
    similar_users = user_similarity_cosine_df[user_similarity_cosine_df[picked_userid] > user_similarity_threshold][picked_userid].sort_values(ascending=False)[:n]

    # Books that Targeted User has Read
    picked_userid_watched = matrix_norm[matrix_norm.index == picked_userid].dropna(axis=1, how='all')
    # Books that similar Users read.remove books that none of the similar users have read
    similar_users_books = matrix_norm[matrix_norm.index.isin(similar_users.index)].loc[:, :]
    similar_users_books.drop(picked_userid_watched.columns, axis = 1, inplace = True, errors = 'ignore')
    

    # A dictionary to store item scores
    item_score = {}

    # Initialize the item_score dictionary with book titles as keys and 'book_score' values as 0
    for i in similar_users_books.columns:
        item_score[i] = {'title': i[0], 'description': i[1], 'isbn': i[2], 'author': i[3], 'image' : i[4], 'book_pdf' : i[5], 'book_score': 0}

    # Loop through items
    for i in similar_users_books.columns:
        # Get the rating for book i
        book_rating = similar_users_books[i]
        # Create variables to store the score and count
        total = 0
        count = 0
        # Loop through similar users
        for u in similar_users.index:
            # If the user has rated the book
            if u in book_rating.index and pd.isna(book_rating[u]) == False:

                # Calculate the score
                score = similar_users[u] * book_rating[u]
                # Add the score to the total
                total += score
                # Increment the count
                count += 1
        # Calculate the average score for the book, if count is greater than zero
        if count > 0:
            item_score[i]['book_score'] = total / count

    # Convert the dictionary to a dataframe
    item_score_df = pd.DataFrame.from_dict(item_score, orient='index')

    # Sort the books by score
    ranked_item_score = item_score_df.sort_values(by='book_score', ascending=False)

    # Select the top m books
    m = 10
    top_books = ranked_item_score.head(m)
    print(top_books) 
    # Render the recommendations template with the top_books as context
    return render(request, 'books/recom_result.html', {'top_books': top_books})


#Item based collaborative filtering
# 
# def recommend(request):
#     # Fetch data from database and store in dataframes
#     df_books = pd.DataFrame(list(Pdf_Info.objects.all().values()))
#     df_books.dropna(inplace=True)
#     df_reviews = pd.DataFrame(list(Review.objects.all().values()))
#     df_books.fillna(0, inplace=True)
#     df_reviews.fillna(0, inplace=True)

#     # Merge dataframes to create a single ratings dataframe
#     ratings_with_name = df_reviews.merge(df_books, on='isbn')

#     # Filter ratings and books to only include users and books with sufficient ratings
#     x = ratings_with_name.groupby('created_by_id').count()['rating'] > 3
#     read_users = x[x].index
#     filtered_rating = ratings_with_name[ratings_with_name['created_by_id'].isin(read_users)]
#     y = filtered_rating.groupby('title').count()['rating'] >= 2
#     famous_books = y[y].index
#     final_ratings = filtered_rating[filtered_rating['created_by_id'].isin(read_users) & filtered_rating['title'].isin(famous_books)]

#     # Create pivot table with ratings as values
#     pt = final_ratings.pivot_table(index='title', columns='created_by_id', values='rating')
#     # Replace NaN values with mean rating of the book
#     pt = pt.apply(lambda row: row.fillna(row.mean()), axis=1)

#     if request.method == 'POST':
#         # Fetch user input
#         user_input = request.POST.get('user_input')

#         if user_input is not None:
#             # Get indices of books that match the user query
#             match_indices = np.where(pt.index.str.contains(user_input, case=False))[0]

#             if len(match_indices) > 0:
#                 # Get similarity scores for all books
#                 similarity_scores = cosine_similarity(pt)

#                 # Get indices of similar books with the same genre as the searched book
#                 similar_items = []
#                 for i in range(similarity_scores.shape[0]):
#                     if i in match_indices:
#                         # Check if book has the same genre as the searched book
#                         if df_books.loc[df_books['title'] == pt.index[i], 'genre_id'].iloc[0] == df_books.loc[df_books['title'] == pt.index[match_indices[-1]], 'genre_id'].iloc[0]:
#                             # Append index and similarity score to list
#                             if i != match_indices[-1]:
#                                 similar_items.append((i, similarity_scores[match_indices[-1]][i]))

#                 # Sort by similarity score
#                 similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)[:9]

#                 # Get book information and append to list
#                 data = []
#                 for i in similar_items:
#                     item = []
#                     temp_df = df_books[df_books['title'] == pt.index[i[0]]]
#                     item.extend(list(temp_df.drop_duplicates('title')['title'].values))
#                     item.extend(list(temp_df.drop_duplicates('title')['author'].values))
#                     item.extend(list(temp_df.drop_duplicates('title')['image'].values))
#                     data.append(item)
#             else:
#                 messages.info(request, 'Recommendations not found')
#                 data = []
#         else:
#             messages.info(request, 'Please enter a book name')
#             data = []

#         context = {
#             'data' : data
#         }

#         return render(request, 'books/recommendation.html', context)

#     return render(request, 'books/recommendation.html')


def recommend(request):
    # Fetch data from database and store in dataframes
    df_books = pd.DataFrame(list(Pdf_Info.objects.all().values()))
    df_books.dropna(inplace=True)
    df_reviews = pd.DataFrame(list(Review.objects.all().values()))
    df_books.fillna(0, inplace=True)
    df_reviews.fillna(0, inplace=True)

    # Merge dataframes to create a single ratings dataframe
    ratings_with_name = df_reviews.merge(df_books, on='isbn')

    # Filter ratings and books to only include users and books with sufficient ratings
    x = ratings_with_name.groupby('created_by_id').count()['rating'] > 3
    read_users = x[x].index
    filtered_rating = ratings_with_name[ratings_with_name['created_by_id'].isin(read_users)]
    y = filtered_rating.groupby('title').count()['rating'] >= 2
    famous_books = y[y].index
    final_ratings = filtered_rating[filtered_rating['created_by_id'].isin(read_users) & filtered_rating['title'].isin(famous_books)]

    # Create pivot table with ratings as values
    pt = final_ratings.pivot_table(index='title', columns='created_by_id', values='rating')
    # Replace NaN values with mean rating of the book
    pt = pt.apply(lambda row: row.fillna(row.mean()), axis=1)

    if request.method == 'POST':
        # Fetch user input
        user_input = request.POST.get('user_input')

        if user_input is not None:
            # Get indices of books that match the user query
            match_indices = np.where(pt.index.str.contains(user_input, case=False))[0]

            if len(match_indices) > 0:
                # Get similarity scores for all books
                similarity_scores = cosine_similarity(pt)

                # Get indices of similar books with the same genre as the searched book
                similar_items = []
                for i in range(similarity_scores.shape[0]):
                    if i in match_indices:
                        # Check if book has the same genre as the searched book
                        if df_books.loc[df_books['title'] == pt.index[i], 'genre_id'].iloc[0] == df_books.loc[df_books['title'] == pt.index[match_indices[-1]], 'genre_id'].iloc[0]:
                            # Append index and similarity score to list
                            if i != match_indices[-1]:
                                similar_items.append((i, similarity_scores[match_indices[-1]][i]))

                # Sort by similarity score
                similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)[:9]

                # Get book information and append to list
                data = []
                for i in similar_items:
                    item = {}
                    temp_pdf_info = ratings_with_name[ratings_with_name['isbn'] == final_ratings[final_ratings['title'] == pt.index[i[0]]]['isbn'].iloc[0]]
                    # temp_pdf_info = df_books[df_books['isbn'] == final_ratings[final_ratings['title'] == pt.index[i[0]]]['isbn'].iloc[0]]
                    if len(temp_pdf_info) == 0:
                        continue
                    item['title'] = temp_pdf_info.iloc[0]['title']
                    item['author'] = temp_pdf_info.iloc[0]['author']
                    item['image'] = temp_pdf_info.iloc[0]['image']
                    item['description'] = temp_pdf_info.iloc[0]['description']
                    item['isbn'] = temp_pdf_info.iloc[0]['isbn']
                    item['published_year'] = temp_pdf_info.iloc[0]['published_year']
                    item['book_pdf'] = temp_pdf_info.iloc[0]['book_pdf']
                    item['is_premium'] = temp_pdf_info.iloc[0]['is_premium']
                    # item['rating'] = temp_pdf_info.iloc[0]['rating']
                    # item['content'] = temp_pdf_info.iloc[0]['content']
                    # item['created_at'] = temp_pdf_info.iloc[0]['created_at']
                    # item['created_by_id'] = temp_pdf_info.iloc[0]['created_by_id']

                    item['reviews'] = []
                    book_isbn = df_books[df_books['title'] == pt.index[i[0]]]['isbn'].iloc[0]
                    book_reviews = df_reviews[df_reviews['isbn'] == book_isbn]
                    print(book_reviews)
                    for review in book_reviews.itertuples():
                        temp_review = {}
                        temp_review['rating'] = review.rating
                        temp_review['content'] = review.content
                        temp_review['created_at'] = review.created_at
                        temp_review['created_by'] = review.created_by_id
                        item['reviews'].append(temp_review)
                    
                    if len(item['reviews']) > 0:
                        item['avg_rating'] = round(sum([review['rating'] for review in item['reviews']]) / len(item['reviews']), 1)
                    else:
                        item['avg_rating'] = 0
                    data.append(item)
                    data = sorted(data, key=lambda x: x['avg_rating'], reverse=True)
            else:
                messages.info(request, 'Recommendations not found')
                data = []
        else:
            messages.info(request, 'Please enter a book name')
            data = []

        context = {
            'data' : data
        }

        return render(request, 'books/recommendation.html', context)

    return render(request, 'books/recommendation.html')

