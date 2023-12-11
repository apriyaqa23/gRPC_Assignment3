import grpc
import config_pb2_grpc
import config_pb2

class RedditClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = config_pb2_grpc.RedditServiceStub(self.channel)

    def create_post(self, post_data):
        # Create a Post using gRPC stub
        return self.stub.CreatePost(post_data)

    def vote_post(self, post_id, upvote):
        # Vote on a Post using gRPC stub
        request = config_pb2.VotePostRequest(post_id=post_id, upvote=upvote)
        return self.stub.VotePost(request)

    def get_post(self, post_id):
        # Retrieve a Post using gRPC stub
        request = config_pb2.GetPostRequest(post_id=post_id)
        return self.stub.GetPost(request)

    def create_comment(self, post_id, comment_data):
        # Create a Comment using gRPC stub
        request = config_pb2.CreateCommentRequest(post_id=post_id, comment=comment_data)
        return self.stub.CreateComment(request)

    def vote_comment(self, comment_id, upvote):
        # Vote on a Comment using gRPC stub
        request = config_pb2.VoteCommentRequest(comment_id=comment_id, upvote=upvote)
        return self.stub.VoteComment(request)

    def get_most_upvoted_comments(self, post_id, N):
        # Retrieve N most upvoted comments under a post using gRPC stub
        request = config_pb2.GetMostUpvotedCommentsRequest(post_id=post_id, N=N)
        return self.stub.GetMostUpvotedComments(request)

    def expand_comment_branch(self, comment_id, N):
        # Expand a comment branch with a depth of 2 using gRPC stub
        request = config_pb2.ExpandCommentBranchRequest(comment_id=comment_id, N=N)
        return self.stub.ExpandCommentBranch(request)

    # Extra Credit
    def monitor_updates(self, post_id, comment_ids):
        # Monitor updates for a post and its comments using gRPC stub
        request = config_pb2.MonitorUpdatesRequest(post_id=post_id, comment_ids=comment_ids)
        return self.stub.MonitorUpdates(request)

if __name__ == '__main__':
    client = RedditClient('localhost', 50051)
