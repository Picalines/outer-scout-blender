from bpy.types import Context

def show_message_popup(context: Context, message: str, *, title = 'Message Box', icon = 'INFO'):

    def draw(self, _):
        self.layout.label(text=message)

    context.window_manager.popup_menu(draw, title=title, icon=icon)
