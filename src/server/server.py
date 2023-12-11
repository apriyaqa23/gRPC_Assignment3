import argparse
from concurrent import futures
import grpc
import config_pb2_grpc
import config_pb2
import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('reddit.db')
cursor = conn.cursor()

# Create tables for posts and comments
cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        post_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        text TEXT,
        author TEXT
    )
''')

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
conn.close()
posts={}
comments ={}
subreddits = {}

# Dummy authentication function (always grants access)
def dummy_auth(request, context):
    pass

class RedditServiceServicer(config_pb2_grpc.RedditServiceServicer):
    def CreatePost(self, request, context):
        new_post = config_pb2.Post(
            title=request.title,
            text=request.text,
            author=request.author,
            video_url=request.video_url,
            image_url=request.image_url,
            score=0,  # Initial score for a new post
            state=config_pb2.Post.NORMAL,  # Initial state is normal
            subreddit_name=request.subreddit_name,  # Assuming subreddit name is provided
            tags=request.tags  # Assuming tags are provided
        )
        posts[new_post.post_id] = new_post  # Storing the post in the dictionary
        return new_post  # Return the created Post object

    def GetPost(self, request, context):
        post = posts.get(request.post_id)
        if post:
            return post  # Return the post if found
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Post not found")
            return config_pb2.Post()  # Return an empty Post object or handle error as per requirement

    def VotePost(self, request, context):
        post = posts.get(request.post_id)
        if post:
            if request.upvote:
                post.score += 1  # Upvote
            else:
                post.score -= 1  # Downvote
            return post  # Return the updated Post object
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Post not found")
            return config_pb2.Post()  # Return an empty Post object or handle error as per requirement

    def CreateComment(self, request, context):
        # Implement logic to create a comment under a post
        new_comment = config_pb2.Comment(
            text=request.text,
            author=request.author,
            score=0,  # Initial score for a new comment
            state=config_pb2.Comment.NORMAL,  # Assuming comments start in a normal state
            # Publication date will be set automatically
        )
        comments[new_comment.comment_id] = new_comment  # Storing the comment in the dictionary
        return new_comment  # Return the created Comment object

    def VoteComment(self, request, context):
        # Implement logic to vote on a comment
        comment = comments.get(request.comment_id)
        if comment:
            if request.upvote:
                comment.score += 1  # Upvote
            else:
                comment.score -= 1  # Downvote
            return comment  # Return the updated Comment object
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Comment not found")
            return config_pb2.Comment()  # Return an empty Comment object or handle error as per requirement

    def GetMostUpvotedComments(self, request, context):
        # Retrieve comments for the given post
        post_comments = [comment for comment in comments.values() if comment.post_id == request.post_id]

        # Sort comments by score (descending order)
        sorted_comments = sorted(post_comments, key=lambda x: x.score, reverse=True)

        # Get N most upvoted comments
        most_upvoted_comments = sorted_comments[:request.N]

        # Check if each comment has replies (dummy logic)
        has_replies = [True if comment.comment_id in comments else False for comment in most_upvoted_comments]

        # Return the most upvoted comments and whether they have replies
        return config_pb2.GetMostUpvotedCommentsResponse(
            comments=most_upvoted_comments,
            has_replies=has_replies
        )

    def ExpandCommentBranch(self, request, context):
        # Get the root comment
        root_comment = comments.get(request.comment_id)

        if not root_comment:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Root comment not found")
            return config_pb2.ExpandCommentBranchResponse()  # Return an empty response or handle error

        # Retrieve comments under the root comment (replies)
        child_comments = [comment for comment in comments.values() if comment.parent_id == root_comment.comment_id]

        return config_pb2.ExpandCommentBranchResponse(
               comments=child_comments,
               has_replies=[True if comment.comment_id in comments else False for comment in child_comments]
        )
    # Extra Credit
    def MonitorUpdates(self, request, context):
        # Continuously monitor updates for the given post and its comments
        while True:
           # Fetch and return updated scores periodically (dummy logic)
           yield config_pb2.MonitorUpdatesResponse(
           post=posts.get(request.post_id),
           comments=[comments.get(comment_id) for comment_id in request.comment_ids])


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    config_pb2_grpc.add_RedditServiceServicer_to_server(RedditServiceServicer(), server)
    server.add_insecure_port(f'[::]:{port}')  # Set port based on input argument
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start Reddit gRPC server')
    parser.add_argument('-p', '--port', type=int, default=50051, help='Port number for the server (default: 50051)')
    args = parser.parse_args()
    serve(args.port)
