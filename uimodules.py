import tornado.web


class Thread(tornado.web.UIModule):
    def render(self, thread, autosage):
        return self.render_string('modules/thread.html', thread=thread, autosage=autosage)


class CatalogThread(tornado.web.UIModule):
    def render(self, thread):
        return self.render_string('modules/catalog.html', thread=thread)


class NewPost(tornado.web.UIModule):
    def javascript_files(self):
        return('js/validate_file.js')
    def render(self, name, admin, show):
        return self.render_string('modules/newpost.html', name=name, admin=admin, show=show)


class Post(tornado.web.UIModule):
    def render(self, post, admin):
        return self.render_string('modules/post.html', post=post, admin=admin)


class Preview(tornado.web.UIModule):
    def render(self, post):
        return self.render_string('modules/post_preview.html', post=post)


class OpPost(tornado.web.UIModule):
    def render(self, op, admin):
        return self.render_string('modules/oppost.html', op=op, admin=admin)


class Board(tornado.web.UIModule):
    def render(self, board):
        return self.render_string('modules/board.html', board=board)


class Image(tornado.web.UIModule):
    def render(self, image, objectid, thumb):
        return self.render_string('modules/image.html', image=image, objectid=objectid, thumb=thumb)


class Video(tornado.web.UIModule):
    def render(self, video, objectid, thumb):
        return self.render_string('modules/video.html', video=video, objectid=objectid, thumb=thumb)


class Audio(tornado.web.UIModule):
    def render(self, audio, objectid):
        return self.render_string('modules/audio.html', audio=audio, objectid=objectid)


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


class Ban(tornado.web.UIModule):
    def css_files(self):
        return 'css/modules/banned.css'
    def render(self, ban):
        return self.render_string('modules/banned.html', b=ban)


class Settings(tornado.web.UIModule):
    def css_files(self):
        return 'css/modules/settings.css'
    def render(self):
        return self.render_string('modules/settings.html')


class Template(tornado.web.UIModule):
    def render(self):
        return self.render_string('modules/template.html')
