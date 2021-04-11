import tornado.web


class Thread(tornado.web.UIModule):
    def render(self, thread, thread_bump, postcount, current_user):
        autosage = thread_bump <= postcount
        return self.render_string('modules/thread.html', thread=thread, autosage=autosage, current_user=current_user)


class CatalogThread(tornado.web.UIModule):
    def render(self, thread, current_user):
        return self.render_string('modules/catalog.html', thread=thread, current_user=current_user)


class NewPost(tornado.web.UIModule):
    def javascript_files(self):
        return('js/validate_file.js')
    def render(self, name, admin, show, current_user):
        return self.render_string('modules/newpost.html', name=name, admin=admin, show=show, current_user=current_user)


class Post(tornado.web.UIModule):
    def render(self, post, admin, current_user):
        return self.render_string('modules/post.html', post=post, admin=admin, current_user=current_user)


class Preview(tornado.web.UIModule):
    def render(self, post, current_user):
        return self.render_string('modules/post_preview.html', post=post, current_user=current_user)


class OpPost(tornado.web.UIModule):
    def render(self, op, admin, autosage, current_user):
        return self.render_string('modules/oppost.html', op=op, admin=admin, autosage=autosage, current_user=current_user)


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


class Pinned(tornado.web.UIModule):
    def render(self, thread):
        return self.render_string('modules/pinned.html', thread=thread)


class SearchResult(tornado.web.UIModule):
    def render(self, post, count):
        return self.render_string('modules/searchresult.html', post=post, count=count)


