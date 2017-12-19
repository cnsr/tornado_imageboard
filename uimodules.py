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
    def render(self, post, admin):
        return self.render_string('modules/post.html', post=post, admin=admin)


class OpPost(tornado.web.UIModule):
    def render(self, op, admin):
        return self.render_string('modules/oppost.html', op=op, admin=admin)


class Board(tornado.web.UIModule):
    def render(self, board):
        return self.render_string('modules/board.html', board=board)


class Image(tornado.web.UIModule):
    def render(self, image, objectid):
        return self.render_string('modules/image.html', image=image, objectid=objectid)


class Video(tornado.web.UIModule):
    def render(self, video, objectid):
        return self.render_string('modules/video.html', video=video, objectid=objectid)


class Modal(tornado.web.UIModule):
    def javascript_files(self):
        return 'js/modal.js'
    def css_files(self):
        return 'css/modules/modal.css'
    def render(self):
        return self.render_string('modules/modal.html')

class Stats(tornado.web.UIModule):
    def css_files(self):
        return 'css/modules/stats.css'
    def render(self, board):
        return self.render_string('modules/stats.html', b=board)
