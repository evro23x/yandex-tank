from Tank.Plugins.Aggregator import AggregatorPlugin, AggregateResultListener
from Tank.Plugins.ConsoleScreen import Screen
from tankcore import AbstractPlugin
import logging
import sys
import traceback


class ConsoleOnlinePlugin(AbstractPlugin, AggregateResultListener):
    SECTION = 'console'
    
    def __init__(self, core):
        AbstractPlugin.__init__(self, core)
        self.screen = None
        self.render_exception = None
        self.console_markup = None
        self.remote_translator = None

    @staticmethod
    def get_key():
        return __file__
    
    def configure(self):
        self.info_panel_width = self.get_option("info_panel_width", '33')
        self.short_only = int(self.get_option("short_only", '0'))
        if sys.stdout.isatty() and not int(self.get_option("disable_all_colors", '0')):
            self.console_markup = RealConsoleMarkup()
        else:
            self.console_markup = NoConsoleMarkup()
        for color in self.get_option("disable_colors", '').split(' '):
            self.console_markup.__dict__[color] = ''
        self.screen = Screen(self.info_panel_width, self.console_markup)

        try:
            aggregator = self.core.get_plugin_of_type(AggregatorPlugin)
            aggregator.add_result_listener(self)
        except KeyError:
            self.log.debug("No aggregator for console")
            self.screen.block_rows=[]
            self.screen.info_panel_percent=100

    def is_test_finished(self):
        try:
            console_view = self.screen.render_screen().encode('utf-8')
        except Exception, ex:
            self.log.warn("Exception inside render: %s", traceback.format_exc(ex))
            self.render_exception = ex
            console_view = ""

        if console_view:
            if not self.short_only:
                sys.stdout.write(self.console_markup.clear)
                sys.stdout.write(console_view)
                sys.stdout.write(self.console_markup.TOTAL_RESET)
        
            if self.remote_translator:
                self.remote_translator.send_console(self.console_markup.clean_markup(console_view))

        return -1
    
    def aggregate_second(self, second_aggregate_data):
        if self.short_only:
            tpl = "Time: %s\tExpected RPS: %s\tActual RPS: %s\tActive Threads: %s\tAvg RT: %s"
            o = second_aggregate_data.overall # just to see the next line in IDE
            data = (second_aggregate_data.time, o.planned_requests, o.RPS,
                    o.active_threads, o.avg_response_time)
            self.log.info(tpl % data)
        else:
            self.screen.add_second_data(second_aggregate_data)    
            #self.is_test_finished()

    
    def add_info_widget(self, widget):
        if not self.screen:
            self.log.debug("No screen instance to add widget")
        else:
            self.screen.add_info_widget(widget)
        
# ======================================================

class RealConsoleMarkup(object):
    '''    
    Took colors from here: https://www.siafoo.net/snippet/88
    '''
    WHITE_ON_BLACK = '\033[37;40m'
    TOTAL_RESET = '\033[0m'
    clear = "\x1b[2J\x1b[H"
    new_line = "\n"
    
    YELLOW = '\033[1;33m'
    RED = '\033[1;31m'
    RED_DARK = '\033[31;3m'
    RESET = '\033[1;m'
    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    WHITE = "\033[1;37m"
    MAGENTA = '\033[1;35m'
    BG_MAGENTA = '\033[1;45m'
    BG_GREEN = '\033[1;42m'
    BG_BROWN = '\033[1;43m'
    BG_CYAN = '\033[1;46m'
    
    def clean_markup(self, orig_str):
        for val in [self.YELLOW, self.RED, self.RESET,
                    self.CYAN, self.BG_MAGENTA, self.WHITE,
                    self.BG_GREEN, self.GREEN, self.BG_BROWN,
                    self.RED_DARK, self.MAGENTA, self.BG_CYAN]:
            orig_str = orig_str.replace(val, '')
        return orig_str

# ======================================================

# FIXME: 3 better way to have it?
class NoConsoleMarkup(RealConsoleMarkup):
    WHITE_ON_BLACK = ''
    TOTAL_RESET = ''
    clear = ""
    new_line = "\n"
    
    YELLOW = ''
    RED = ''
    RED_DARK = ''
    RESET = ''
    CYAN = ""
    GREEN = ""
    WHITE = ""
    MAGENTA = ''
    BG_MAGENTA = ''
    BG_GREEN = ''
    BG_BROWN = ''
    BG_CYAN = ''

# ======================================================


class AbstractInfoWidget:
    def __init__(self):
        self.log = logging.getLogger(__name__)

    def render(self, screen):
        self.log.warn("Please, override render widget")
        return "[Please, override render widget]"

    def get_index(self):
        return 0;

