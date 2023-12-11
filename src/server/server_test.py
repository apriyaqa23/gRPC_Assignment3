import sqlite3
from unittest.mock import MagicMock

import config_pb2
import config_pb2_grpc
import grpc

conn = sqlite3.connect('reddit.db')
cursor = conn.cursor()

def create_stub():
    channel = grpc.insecure_channel('localhost:50051')
    return config_pb2_grpc.RedditServiceStub(channel)
def create_post_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            text TEXT,
            author TEXT
        )
    ''')
    conn.commit()


def create_post(title, text, author):
    try:
        cursor.execute("INSERT INTO posts (title, text, author) VALUES (?, ?, ?)", (title, text, author))
        conn.commit()
        print("Post created successfully!")
    except sqlite3.Error as e:
        print("Error creating post:", e)
        conn.rollback()

def retrieve_post(post_id):
    try:
        cursor.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,))
        post_data = cursor.fetchone()  # Fetch the post data
        if post_data:
            post = {
                'post_id': post_data[0],
                'title': post_data[1],
                'text': post_data[2],
                'author': post_data[3]
            }
            return post
        else:
            print("Post not found.")
            return None
    except sqlite3.Error as e:
        print("Error retrieving post:", e)
        return None
def create_comment_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INTEGER PRIMARY KEY,
            post_id INTEGER,
            text TEXT,
            author TEXT,
            FOREIGN KEY(post_id) REFERENCES posts(post_id)
        )
    ''')
    conn.commit()

def create_comment(post_id, text, author):
    try:
        cursor.execute("INSERT INTO comments (post_id, text, author) VALUES (?, ?, ?)", (post_id, text, author))
        conn.commit()
        print("Comment created successfully!")
    except sqlite3.Error as e:
        print("Error creating comment:", e)
        conn.rollback()

def add_comment_to_post(post_id, text, author):
    try:
        cursor.execute("INSERT INTO comments (post_id, text, author) VALUES (?, ?, ?)", (post_id, text, author))
        conn.commit()
        print("Comment added to post successfully!")
    except sqlite3.Error as e:
        print("Error adding comment to post:", e)
        conn.rollback()

def get_most_upvoted_comments(post_id, limit):
    try:
        cursor.execute(
            "SELECT * FROM comments WHERE post_id = ? ORDER BY score DESC LIMIT ?",
            (post_id, limit)
        )
        comments_data = cursor.fetchall()
        comments = []
        for comment_data in comments_data:
            comment = {
                'comment_id': comment_data[0],
                'post_id': comment_data[1],
                'text': comment_data[2],
                'author': comment_data[3],
                'score': comment_data[4],
                'state': comment_data[5]
            }
            comments.append(comment)
        return comments
    except sqlite3.Error as e:
        print("Error retrieving comments:", e)
        return None

def expand_comment_branch(comment_id):
    channel = grpc.insecure_channel('localhost:50051')
    stub = config_pb2_grpc.RedditServiceStub(channel)

    # Create a request to expand comment branch
    request = config_pb2.ExpandCommentBranchRequest(comment_id=comment_id, N=10)

    try:
        # Call the ExpandCommentBranch method
        response = stub.ExpandCommentBranch(request)
        print("Expanded Comment Branch:")
        print(response)  # Handle the response data accordingly
    except grpc.RpcError as e:
        print(f"Error expanding comment branch: {e.details()}")

def get_most_upvoted_reply(api_client):
    try:
        most_upvoted_comments_request = config_pb2.GetMostUpvotedCommentsRequest(post_id=1, N=1)
        response = api_client.GetMostUpvotedComments(most_upvoted_comments_request)

        if response.comments:
            most_upvoted_comment = response.comments[0]
            replies_request = config_pb2.ExpandCommentBranchRequest(comment_id=most_upvoted_comment.comment_id, N=1)
            replies_response = api_client.ExpandCommentBranch(replies_request)

            if replies_response.comments:
                sorted_replies = sorted(replies_response.comments, key=lambda x: x.score, reverse=True)
                return sorted_replies[0]
            else:
                print("No replies under the most upvoted comment.")
                return None
        else:
            print("No comments for the post.")
            return None
    except grpc.RpcError as e:
        print(f"Error getting most upvoted reply: {e}")
        return None

def test_get_most_upvoted_reply():
    stub = MagicMock()

    expected_reply = config_pb2.Comment(
        comment_id=1,
        text="Mock reply text",
        author="Mock author",
        score=5,
        state=config_pb2.Comment.NORMAL
    )

    # Set up the stub's GetMostUpvotedComments method to return a predefined comment
    stub.GetMostUpvotedComments.return_value = config_pb2.GetMostUpvotedCommentsResponse(
        comments=[expected_reply],
        has_replies=[False]
    )

    # Set up the stub's ExpandCommentBranch method to return predefined replies
    stub.ExpandCommentBranch.return_value = config_pb2.ExpandCommentBranchResponse(
        comments=[expected_reply],
        has_replies=[False]
    )

    actual_reply = get_most_upvoted_reply(stub)
    assert actual_reply == expected_reply

if __name__ == '__main__':
    # Post Operations
    create_post_table()
    create_post("Sample Title", "Sample text content for the post.", "John Doe")
    print(retrieve_post(1))# Retrieve post using db success!

    # Comment Operations
    create_comment_table()
    create_comment(1, "Sample comment text.", "Alice")
    create_comment(1, "Another comment.", "Bob")

    #Get most upvoted comments under a post
    add_comment_to_post(1, "Comment 1", "Alice")
    add_comment_to_post(1, "Comment 2", "Bob")
    most_upvoted_comments = get_most_upvoted_comments(1, 5)
    if most_upvoted_comments:
        print("Most upvoted comments for post 1:")
        for comment in most_upvoted_comments:
            print(comment)
    else:
        print("No comments found for the post.")

    # Expand the most upvoted comment
    expand_comment_branch(comment_id="1")

    #Return the most upvoted reply under the most upvoted comment
    stub = create_stub()
    most_upvoted_reply = get_most_upvoted_reply(stub)
    if most_upvoted_reply:
        print("Most upvoted reply:", most_upvoted_reply)
    else:
        print("No most upvoted reply found.")
    test_get_most_upvoted_reply()
