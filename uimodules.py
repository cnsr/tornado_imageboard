import tornado.web


class Thread(tornado.web.UIModule):
    def render(self, thread):
        return self.render_string(
            'modules/thread.html', thread=thread)


class NewPost(tornado.web.UIModule):
    def javascript_files(self):
        return('js/validate_file.js')
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


class Image(tornado.web.UIModule):
    def render(self, image, objectid):
        return self.render_string('modules/image.html', image=image, objectid=objectid)


class Video(tornado.web.UIModule):
    def render(self, video, objectid):
        return self.render_string('modules/video.html', video=video, objectid=objectid)

