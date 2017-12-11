import tornado.web


class Thread(tornado.web.UIModule):
    def render(self, thread):
        return self.render_string(
            'modules/thread.html', thread=thread)


class NewPost(tornado.web.UIModule):
    def render(self):
        return self.render_string('modules/newpost.html')


class Post(tornado.web.UIModule):
    def render(self, post):
        return self.render_string('modules/post.html', post=post)


class OpPost(tornado.web.UIModule):
    def render(self, op):
        return self.render_string('modules/oppost.html', op=op)


class Board(tornado.web.UIModule):
    def render(self, board):
        return self.render_string('modules/board.html', board=board)

